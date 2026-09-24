import base64
import hashlib
import imaplib
import re
from datetime import date, datetime
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from app.collectors.base import CollectionResult, Collector
from app.config import get_settings
from app.jobs.candidate import CandidateSource, JobCandidate
from app.schedules import RecruitmentScheduleCandidate


class NaverMailCollector(Collector):
    """Collect allowed job-alert emails from a user-authorized Naver IMAP mailbox."""

    source = "NAVER_IMAP"

    def __init__(
        self,
        username: str | None = None,
        app_password: str | None = None,
        mailbox: str | None = None,
        allowed_senders: str | None = None,
        max_messages: int | None = None,
        processed_mail_keys: set[tuple[str, str]] | None = None,
        imap_client: Any | None = None,
    ) -> None:
        super().__init__()
        settings = get_settings()
        self.host = settings.naver_imap_host
        self.port = settings.naver_imap_port
        self.username = username if username is not None else settings.naver_imap_username
        self.app_password = app_password if app_password is not None else settings.naver_imap_app_password
        self.mailboxes = self.mailbox_names(mailbox or settings.naver_imap_mailbox)
        self.mailbox = self.mailboxes[0]
        sender_value = allowed_senders if allowed_senders is not None else settings.naver_imap_allowed_senders
        self.allowed_senders = {sender.strip().lower() for sender in sender_value.split(",") if sender.strip()}
        self.max_messages = max_messages if max_messages is not None else settings.naver_imap_max_messages
        self.processed_mail_keys = processed_mail_keys or set()
        self.imap_client = imap_client

    def collect(self) -> CollectionResult:
        try:
            candidates, schedules = self.fetch_content()
            return CollectionResult(source=self.source, requested_count=len(candidates) + len(schedules), candidates=candidates, schedules=schedules)
        except imaplib.IMAP4.error:
            return CollectionResult(source=self.source, error="네이버 IMAP 인증 또는 연결 설정에 실패했습니다.")
        except (OSError, ValueError, KeyError) as error:
            return CollectionResult(source=self.source, error=str(error))

    def fetch_candidates(self) -> list[JobCandidate]:
        candidates, _ = self.fetch_content()
        return candidates

    def fetch_content(self) -> tuple[list[JobCandidate], list[RecruitmentScheduleCandidate]]:
        if not self.username or not self.app_password:
            raise ValueError("NAVER_IMAP_USERNAME 및 NAVER_IMAP_APP_PASSWORD 설정이 필요합니다.")
        if self.max_messages < 1:
            raise ValueError("NAVER_IMAP_MAX_MESSAGES는 1 이상이어야 합니다.")

        client = self.imap_client or imaplib.IMAP4_SSL(self.host, self.port)
        owns_client = self.imap_client is None
        try:
            status, _ = client.login(self.username, self.app_password)
            if status != "OK":
                raise ValueError("네이버 IMAP 로그인에 실패했습니다.")
            candidates: list[JobCandidate] = []
            schedules: list[RecruitmentScheduleCandidate] = []
            for mailbox in self.mailboxes:
                status, _ = client.select(self.imap_mailbox_name(mailbox), readonly=True)
                if status != "OK":
                    raise ValueError(f"네이버 IMAP 메일함을 열 수 없습니다: {mailbox}")
                uid_validity = self.uid_validity(client)
                status, data = client.uid("search", None, "ALL")
                if status != "OK":
                    raise ValueError("네이버 IMAP 메일 검색에 실패했습니다.")

                uids = data[0].split()[-self.max_messages :]
                for uid_bytes in uids:
                    uid = uid_bytes.decode()
                    mail_key = f"{uid_validity}:{uid}"
                    if (mailbox, mail_key) in self.processed_mail_keys:
                        continue
                    status, message_data = client.uid("fetch", uid, "(RFC822)")
                    if status != "OK" or not message_data or not message_data[0]:
                        raise ValueError(f"네이버 IMAP 메일을 읽을 수 없습니다: uid={uid}")
                    raw_message = message_data[0][1]
                    if not isinstance(raw_message, bytes):
                        raise ValueError(f"네이버 IMAP 메일 형식이 올바르지 않습니다: uid={uid}")
                    message = message_from_bytes(raw_message)
                    candidates.extend(self.to_candidates(message, mail_key, mailbox))
                    if schedule := self.schedule_from_message(message, mail_key, mailbox):
                        schedules.append(schedule)
            return candidates, schedules
        finally:
            if owns_client:
                try:
                    client.logout()
                except (imaplib.IMAP4.error, OSError):
                    pass

    @staticmethod
    def uid_validity(client: Any) -> str:
        response = client.response("UIDVALIDITY")
        values = response[1] if response else None
        if not values or not values[0]:
            raise ValueError("네이버 IMAP UIDVALIDITY를 확인할 수 없습니다.")
        value = values[0]
        return value.decode() if isinstance(value, bytes) else str(value)

    def to_candidates(self, message: Message, mail_key: str, mailbox: str | None = None) -> list[JobCandidate]:
        sender = message.get("From", "").lower()
        sender_address = parseaddr(sender)[1].lower()
        sender_domain = sender_address.rsplit("@", maxsplit=1)[-1]
        if self.allowed_senders and not any(
            sender_domain == allowed_domain or sender_domain.endswith(f".{allowed_domain}")
            for allowed_domain in self.allowed_senders
        ):
            return []

        subject = self.decode_header_value(message.get("Subject", ""))
        message_id = message.get("Message-ID", "").strip()
        candidates = [
            candidate
            for source_url, source_job_id, text, source, platform in self.job_links(message)
            if (candidate := self.candidate_from_listing(
                text, source_url, source_job_id, source, platform, mail_key, message_id, sender, subject, mailbox or self.mailbox
            )) is not None
        ]
        if candidates:
            return candidates
        fallback = self.fallback_candidate(message, mail_key, message_id, sender, subject, mailbox or self.mailbox)
        return [fallback] if fallback is not None else []

    def to_candidate(self, message: Message, mail_key: str, mailbox: str | None = None) -> JobCandidate | None:
        candidates = self.to_candidates(message, mail_key, mailbox)
        return candidates[0] if candidates else None

    def schedule_from_message(self, message: Message, mail_key: str, mailbox: str | None = None) -> RecruitmentScheduleCandidate | None:
        sender_domain = parseaddr(message.get("From", ""))[1].lower().rsplit("@", maxsplit=1)[-1]
        if not sender_domain.endswith("saramin.co.kr"):
            return None
        subject = self.decode_header_value(message.get("Subject", ""))
        match = re.search(r"공채 일정.*?\((\d{1,2})/(\d{1,2})\s*~\s*(\d{1,2})/(\d{1,2})\)", subject)
        if match is None:
            return None
        start_month, start_day, end_month, end_day = (int(value) for value in match.groups())
        year = datetime.now().year
        period_start = date(year, start_month, start_day)
        period_end = date(year + (end_month < start_month), end_month, end_day)
        return RecruitmentScheduleCandidate(
            title="사람인 주간 공채 일정",
            period_start=period_start,
            period_end=period_end,
            source_name="사람인",
            mail_remote_id=mail_key,
            mailbox=mailbox or self.mailbox,
        )

    def candidate_from_listing(
        self,
        text: str,
        source_url: str,
        source_job_id: str,
        source: CandidateSource,
        platform: str,
        mail_key: str,
        message_id: str,
        sender: str,
        subject: str,
        mailbox: str,
    ) -> JobCandidate | None:
        listing = self.parse_listing(text)
        if listing is None:
            return None
        company, title, deadline = listing
        return JobCandidate(
            company=company,
            title=title,
            deadline=deadline,
            status="OPEN",
            source=source,
            source_job_id=source_job_id,
            source_url=source_url,
            raw_metadata=self.mail_metadata(mail_key, message_id, sender, subject, platform, mailbox),
        )

    def fallback_candidate(
        self,
        message: Message,
        mail_key: str,
        message_id: str,
        sender: str,
        subject: str,
        mailbox: str,
    ) -> JobCandidate | None:
        body = self.message_text(message)
        source_url, source_job_id, source, platform = self.job_link(body, sender, message_id or mail_key)

        company = self.field_value(body, "회사명", "기업명", "회사") or self.company_from_subject(subject)
        title = self.field_value(body, "채용제목", "공고명", "모집분야", "포지션") or self.title_from_subject(subject)
        if not company or not title:
            return None

        return JobCandidate(
            company=company,
            title=title,
            location=self.field_value(body, "근무지역", "근무지"),
            experience_type=self.field_value(body, "경력", "경력사항"),
            employment_type=self.field_value(body, "고용형태", "근무형태"),
            deadline=self.parse_date(self.field_value(body, "마감일", "접수마감")),
            status="OPEN",
            source=source,
            source_job_id=source_job_id,
            source_url=source_url,
            raw_metadata=self.mail_metadata(mail_key, message_id, sender, subject, platform, mailbox),
        )

    def mail_metadata(self, mail_key: str, message_id: str, sender: str, subject: str, platform: str, mailbox: str) -> dict[str, str | None]:
        return {
            "mail_provider": "NAVER",
            "mailbox": mailbox,
            "mail_key": mail_key,
            "message_id": message_id or None,
            "sender": sender,
            "subject": subject,
            "source_platform": platform,
        }

    @staticmethod
    def mailbox_names(value: str) -> tuple[str, ...]:
        names = tuple(name.strip() for name in value.split(",") if name.strip())
        if not names:
            raise ValueError("NAVER_IMAP_MAILBOX에 하나 이상의 메일함을 설정해야 합니다.")
        return names

    @staticmethod
    def imap_mailbox_name(mailbox: str) -> str:
        encoded: list[str] = []
        non_ascii: list[str] = []

        def flush_non_ascii() -> None:
            if non_ascii:
                value = "".join(non_ascii).encode("utf-16-be")
                encoded.append("&" + base64.b64encode(value).decode().rstrip("=").replace("/", ",") + "-")
                non_ascii.clear()

        for character in mailbox:
            if " " <= character <= "~" and character != "&":
                flush_non_ascii()
                encoded.append(character)
            elif character == "&":
                flush_non_ascii()
                encoded.append("&-")
            else:
                non_ascii.append(character)
        flush_non_ascii()
        return "".join(encoded)

    @staticmethod
    def decode_header_value(value: str) -> str:
        return "".join(
            part.decode(encoding or "utf-8", errors="replace") if isinstance(part, bytes) else part
            for part, encoding in decode_header(value)
        ).strip()

    @staticmethod
    def message_text(message: Message) -> str:
        parts = message.walk() if message.is_multipart() else [message]
        content: list[str] = []
        for part in parts:
            if part.get_content_maintype() == "multipart" or part.get_content_disposition() == "attachment":
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if part.get_content_type() == "text/html":
                text = re.sub(r"<[^>]+>", " ", text)
            content.append(unescape(text))
        return re.sub(r"[ \t\r\f\v]+", " ", "\n".join(content))

    @staticmethod
    def html_text(message: Message) -> str:
        parts = message.walk() if message.is_multipart() else [message]
        content: list[str] = []
        for part in parts:
            if part.get_content_type() != "text/html" or part.get_content_disposition() == "attachment":
                continue
            payload = part.get_payload(decode=True)
            if payload is not None:
                content.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
        return "\n".join(content)

    def job_links(self, message: Message) -> list[tuple[str, str, str, CandidateSource, str]]:
        links: list[tuple[str, str, str, CandidateSource, str]] = []
        seen_job_ids: set[str] = set()
        parser = _AnchorParser()
        parser.feed(self.html_text(message))
        for href, text in parser.links:
            source_url = self.unwrapped_url(href)
            source_job_id, source, platform = self.source_for_url(source_url)
            if not source_job_id or source_job_id in seen_job_ids:
                continue
            seen_job_ids.add(source_job_id)
            links.append((source_url, source_job_id, text, source, platform))
        return links

    def saramin_job_links(self, message: Message) -> list[tuple[str, str, str]]:
        return [
            (source_url, source_job_id, text)
            for source_url, source_job_id, text, source, _ in self.job_links(message)
            if source is CandidateSource.SARAMIN
        ]

    @staticmethod
    def unwrapped_url(href: str) -> str:
        parsed_url = urlparse(unescape(href))
        wrapped_url = parse_qs(parsed_url.query).get("url", [None])[0]
        return unquote(wrapped_url) if wrapped_url else href

    def parse_listing(self, text: str) -> tuple[str, str, date | None] | None:
        normalized = re.sub(r"\s+", " ", unescape(text)).strip()
        deadline_match = re.search(r"\s*~\s*(상시|20\d{2}[.\-/년 ]\s*\d{1,2}[.\-/월 ]\s*\d{1,2})\s*", normalized)
        if deadline_match is None:
            return None
        deadline = self.parse_date(deadline_match.group(1))
        before_deadline = normalized[: deadline_match.start()].strip()
        after_deadline = normalized[deadline_match.end() :].strip()
        if after_deadline:
            company, title = before_deadline, after_deadline
        elif " - " in before_deadline:
            company, title = before_deadline.split(" - ", maxsplit=1)
        else:
            return None
        if not company or not title:
            return None
        return company[:200].strip(), title[:300].strip(), deadline

    @staticmethod
    def source_for_url(url: str) -> tuple[str | None, CandidateSource, str]:
        parsed_url = urlparse(url)
        hostname = (parsed_url.hostname or "").lower()
        if hostname == "saramin.co.kr" or hostname.endswith(".saramin.co.kr"):
            source_job_id = parse_qs(parsed_url.query).get("rec_idx", [None])[0]
            if "/zf_user/jobs/relay/view" in parsed_url.path and source_job_id:
                return source_job_id, CandidateSource.SARAMIN, "사람인"
        platforms = {
            "jobkorea.co.kr": "잡코리아",
            "wanted.co.kr": "원티드",
            "incruit.com": "인크루트",
            "catch.co.kr": "캐치",
        }
        for domain, platform in platforms.items():
            if hostname == domain or hostname.endswith(f".{domain}"):
                canonical_url = parsed_url._replace(fragment="").geturl()
                source_job_id = f"{domain}-{hashlib.sha256(canonical_url.encode()).hexdigest()[:32]}"
                return source_job_id, CandidateSource.EMAIL, platform
        return None, CandidateSource.EMAIL, "이메일 채용 알림"

    def job_link(self, body: str, sender: str, stable_identifier: str) -> tuple[str | None, str, CandidateSource, str]:
        urls = re.findall(r"https?://[^\s\"<>]+", body)
        for url in urls:
            clean_url = url.rstrip(".,)")
            source_job_id, source, platform = self.source_for_url(clean_url)
            if source_job_id:
                return clean_url, source_job_id, source, platform
        return None, f"mail-{hashlib.sha256(stable_identifier.encode()).hexdigest()[:32]}", CandidateSource.EMAIL, "이메일 채용 알림"

    @staticmethod
    def saramin_job_link(body: str) -> tuple[str | None, str | None]:
        for url in re.findall(r"https?://[^\s\"<>]+", body):
            source_job_id, source, _ = NaverMailCollector.source_for_url(url.rstrip(".,)"))
            if source is CandidateSource.SARAMIN and source_job_id:
                return url.rstrip(".,)"), source_job_id
        return None, None

    @staticmethod
    def field_value(body: str, *labels: str) -> str | None:
        for label in labels:
            match = re.search(rf"{re.escape(label)}\s*[:：]\s*([^\n]+)", body)
            if match:
                value = match.group(1).strip()
                if value:
                    return value[:300]
        return None

    @staticmethod
    def company_from_subject(subject: str) -> str | None:
        match = re.search(r"\[([^\]]+)\]\s*(?:채용|공고)", subject)
        return match.group(1).strip() if match else None

    @staticmethod
    def title_from_subject(subject: str) -> str | None:
        match = re.search(r"(?:채용|공고)\s*[:：-]?\s*(.+)$", subject)
        return match.group(1).strip() if match else None

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        match = re.search(r"(20\d{2})[.\-/년 ]\s*(\d{1,2})[.\-/월 ]\s*(\d{1,2})", value)
        if not match:
            return None
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and self.href is None:
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.text).strip()))
            self.href = None
            self.text = []
