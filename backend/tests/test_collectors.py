import unittest
from email.message import EmailMessage
import imaplib

from app.collectors.alio import AlioCollector
from app.collectors.naver_mail import NaverMailCollector
from app.jobs.normalizer import normalize_candidate


class CollectorMappingTests(unittest.TestCase):
    @staticmethod
    def saramin_message_bytes(identifier: str) -> bytes:
        message = EmailMessage()
        message["From"] = "사람인 <noreply@saramin.co.kr>"
        message["Message-ID"] = f"<{identifier}@example.com>"
        message.set_content(
            "회사명: JOBDA\n"
            "채용제목: 백엔드 개발자\n"
            f"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={identifier}\n"
        )
        return message.as_bytes()

    def test_naver_saramin_mail_mapping_and_normalization(self) -> None:
        message = EmailMessage()
        message["From"] = "사람인 <noreply@saramin.co.kr>"
        message["Subject"] = "[JOBDA] 채용 백엔드 개발자"
        message["Message-ID"] = "<saramin-1@example.com>"
        message.set_content(
            "회사명:  JOBDA \n"
            "채용제목:  백엔드 개발자  \n"
            "근무지역: 서울\n"
            "고용형태: 정규직\n"
            "마감일: 2099.12.31\n"
            "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=12345\n"
        )

        candidate = NaverMailCollector(allowed_senders="saramin.co.kr").to_candidate(message, "10:1")
        self.assertIsNotNone(candidate)
        normalized = normalize_candidate(candidate)
        self.assertEqual(normalized.company, "JOBDA")
        self.assertEqual(normalized.title, "백엔드 개발자")
        self.assertEqual(normalized.status, "OPEN")
        self.assertEqual(normalized.source_job_id, "12345")
        self.assertEqual(normalized.raw_metadata["mail_key"], "10:1")

    def test_naver_mail_ignores_unapproved_sender(self) -> None:
        message = EmailMessage()
        message["From"] = "noreply@example.com"
        message.set_content("회사명: JOBDA\n채용제목: 개발자")

        candidate = NaverMailCollector(allowed_senders="saramin.co.kr").to_candidate(message, "10:1")
        self.assertIsNone(candidate)

    def test_naver_mail_rejects_sender_with_only_matching_suffix_text(self) -> None:
        message = EmailMessage()
        message["From"] = "noreply@not-saramin.co.kr"
        message.set_content("회사명: JOBDA\n채용제목: 개발자")

        candidate = NaverMailCollector(allowed_senders="saramin.co.kr").to_candidate(message, "10:1")

        self.assertIsNone(candidate)

    def test_naver_mail_creates_multiple_candidates_from_html_alert(self) -> None:
        message = EmailMessage()
        message["From"] = "사람인 <noreply@saramin.co.kr>"
        message.set_content(
            "<a href=\"https://api-mail.saramin.co.kr/mail-bridge?url=https%3A%2F%2Fwww.saramin.co.kr%2Fzf_user%2Fjobs%2Frelay%2Fview%3Frec_idx%3D12345\">"
            "JOBDA ~2026-10-01 백엔드 개발자 채용</a>"
            "<a href=\"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=67890\">"
            "JOBDA - 프론트엔드 개발자 채용 ~상시</a>",
            subtype="html",
        )

        candidates = NaverMailCollector(allowed_senders="saramin.co.kr").to_candidates(message, "10:1")

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].source_job_id, "12345")
        self.assertEqual(candidates[0].company, "JOBDA")
        self.assertEqual(candidates[1].title, "프론트엔드 개발자 채용")
        self.assertIsNone(candidates[1].deadline)

    def test_naver_mail_parses_allowed_wanted_link_as_email_source(self) -> None:
        message = EmailMessage()
        message["From"] = "원티드 <noreply@wanted.co.kr>"
        message["Subject"] = "[JOBDA] 채용 백엔드 개발자"
        message["Message-ID"] = "<wanted-1@example.com>"
        message.set_content(
            "회사명: JOBDA\n"
            "채용제목: 백엔드 개발자\n"
            "https://www.wanted.co.kr/wd/12345\n"
        )

        candidate = NaverMailCollector(allowed_senders="wanted.co.kr").to_candidate(message, "10:1")

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.source.value, "EMAIL")
        self.assertEqual(candidate.raw_metadata["source_platform"], "원티드")
        self.assertTrue(candidate.source_job_id.startswith("wanted.co.kr-"))

    def test_naver_imap_skips_processed_uid(self) -> None:
        class FakeImap:
            def login(self, username, password):
                return "OK", []

            def select(self, mailbox, readonly):
                return "OK", []

            def response(self, name):
                return "OK", [b"99"]

            def uid(self, command, *args):
                if command == "search":
                    return "OK", [b"1 2"]
                if command == "fetch":
                    return "OK", [(b"RFC822", CollectorMappingTests.saramin_message_bytes(args[0]))]
                self.fail(f"unexpected IMAP command: {command}")

        collector = NaverMailCollector(
            username="jobda@naver.com",
            app_password="app-password",
            processed_mail_keys={"99:1"},
            imap_client=FakeImap(),
        )

        candidates = collector.fetch_candidates()

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].source_job_id, "2")
        self.assertEqual(candidates[0].raw_metadata["mail_key"], "99:2")

    def test_naver_imap_does_not_return_account_identifier_in_auth_error(self) -> None:
        class AuthFailureImap:
            def login(self, username, password):
                raise imaplib.IMAP4.error(b'[AUTH] "private-account-id": Authentication failed')

        result = NaverMailCollector(
            username="private-account-id",
            app_password="app-password",
            imap_client=AuthFailureImap(),
        ).collect()

        self.assertEqual(result.error, "네이버 IMAP 인증 또는 연결 설정에 실패했습니다.")
        self.assertNotIn("private-account-id", result.error)

    def test_alio_mapping(self) -> None:
        candidate = AlioCollector.to_candidate(
            {
                "instNm": "공공기관",
                "recrutPbancTtl": "개발자",
                "recrutPblntSn": 1,
                "pbancEndYmd": "2099.12.31",
                "ncsCdNmLst": "정보통신",
                "workRgnNmLst": "서울",
                "hireTypeNmLst": "정규직",
                "ongoingYn": "Y",
            }
        )

        self.assertEqual(candidate.company, "공공기관")
        self.assertEqual(candidate.source.value, "ALIO")
        self.assertEqual(candidate.source_job_id, "1")
        self.assertEqual(candidate.job_category, "정보통신")
        self.assertEqual(candidate.status, "진행중")
        self.assertEqual(candidate.company_size, "공공기관")

    def test_alio_uses_official_list_endpoint_and_service_key(self) -> None:
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"resultCode": 200, "resultMsg": "성공했습니다.", "result": []}

        class FakeClient:
            def __init__(self):
                self.request: tuple[str, str, dict[str, object]] | None = None

            def post(self, url, params):
                self.request = ("POST", url, params)
                return FakeResponse()

            def close(self):
                return None

        client = FakeClient()
        collector = AlioCollector(client=client, api_key="test-key", endpoint="https://example.com/list.do")

        self.assertEqual(collector.fetch_candidates(), [])
        self.assertEqual(
            client.request,
            ("POST", "https://example.com/list.do", {"serviceKey": "test-key", "resultType": "json", "ongoingYn": "Y", "pageNo": 1, "numOfRows": 100}),
        )

    def test_alio_collects_all_pages_and_merges_details(self) -> None:
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeClient:
            def __init__(self):
                self.calls: list[tuple[str, dict[str, object]]] = []

            def post(self, url, params):
                self.calls.append((url, params))
                if url.endswith("list.do"):
                    item = {
                        "instNm": "공공기관",
                        "recrutPbancTtl": f"공고 {params['pageNo']}",
                        "recrutPblntSn": params["pageNo"],
                        "ongoingYn": "Y",
                    }
                    return FakeResponse({"resultCode": 200, "result": [item], "totalCount": 2})
                return FakeResponse({"resultCode": 200, "result": {"srcUrl": "https://example.com/posting", "pbancEndYmd": "2099-12-31"}})

            def close(self):
                return None

        client = FakeClient()
        collector = AlioCollector(
            client=client,
            api_key="test-key",
            endpoint="https://example.com/list.do",
            detail_endpoint="https://example.com/detail.do",
            page_size=1,
        )

        candidates = collector.fetch_candidates()

        self.assertEqual([candidate.title for candidate in candidates], ["공고 1", "공고 2"])
        self.assertTrue(all(candidate.source_url == "https://example.com/posting" for candidate in candidates))
        self.assertEqual(len(client.calls), 4)


if __name__ == "__main__":
    unittest.main()
