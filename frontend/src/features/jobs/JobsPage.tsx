import { type ReactNode, useEffect, useState } from "react";

import { getJob, getJobs, Job, JobDetail, User } from "../../api/client";
import PersonalizationPanel from "./PersonalizationPanel";
import PushPanel from "./PushPanel";

type JobsPageProps = {
  user: User;
  onLogout: () => void;
};

const filters = {
  job_category: ["", "Backend", "Frontend", "Data", "DevOps", "Fullstack", "Product"],
  location: ["", "서울", "경기", "부산", "전국"],
  experience: ["", "신입·2년 이하", "1·5년", "2·5년", "3·7년", "경력 무관"],
  employment_type: ["", "정규직", "계약직"],
  company_size: ["", "스타트업", "중소", "중견", "공공기관"],
};

const dashboardBackgrounds = {
  dawn: "/dashboard-dawn.png",
  morning: "/dashboard-morning.png",
  day: "/dashboard-day.png",
  evening: "/dashboard-evening.png",
  night: "/dashboard-night-glass.png",
};

function backgroundForHour(hour: number) {
  if (hour < 6) return dashboardBackgrounds.dawn;
  if (hour < 11) return dashboardBackgrounds.morning;
  if (hour < 16) return dashboardBackgrounds.day;
  if (hour < 20) return dashboardBackgrounds.evening;
  return dashboardBackgrounds.night;
}

type FadeInProps = {
  children: ReactNode;
  delay: number;
  className?: string;
};

function FadeIn({ children, delay, className = "" }: FadeInProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(true), delay);
    return () => window.clearTimeout(timer);
  }, [delay]);

  return <div className={`fade-in ${visible ? "is-visible" : ""} ${className}`} style={{ transitionDuration: "1000ms" }}>{children}</div>;
}

function AnimatedHeading() {
  const [visible, setVisible] = useState(false);
  const lines = ["비전과 행동으로", "내일의 채용을 만듦."];

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(true), 200);
    return () => window.clearTimeout(timer);
  }, []);

  return <h1 className="dashboard-title">
    {lines.map((line, lineIndex) => <span className="dashboard-title-line" key={line}>
      {Array.from(line).map((character, characterIndex) => <span className={`dashboard-title-character ${visible ? "is-visible" : ""}`} key={`${line}-${characterIndex}`} style={{ transitionDelay: `${(lineIndex * line.length + characterIndex) * 30}ms` }}>{character === " " ? "\u00a0" : character}</span>)}
    </span>)}
  </h1>;
}

function formatDeadline(deadline: string) {
  return deadline.replaceAll("-", ".").slice(5);
}

function JobsPage({ user, onLogout }: JobsPageProps) {
  const [currentHour, setCurrentHour] = useState(() => new Date().getHours());
  const [displayBackground, setDisplayBackground] = useState(() => backgroundForHour(new Date().getHours()));
  const [previousBackground, setPreviousBackground] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("latest");
  const [page, setPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<JobDetail | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    const refreshHour = () => setCurrentHour(new Date().getHours());
    const timer = window.setInterval(refreshHour, 60000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const nextBackground = backgroundForHour(currentHour);
    if (nextBackground === displayBackground) return;

    setPreviousBackground(displayBackground);
    setDisplayBackground(nextBackground);
    const timer = window.setTimeout(() => setPreviousBackground(null), 2600);
    return () => window.clearTimeout(timer);
  }, [currentHour, displayBackground]);

  useEffect(() => {
    let cancelled = false;
    setError("");
    getJobs({ q: query, sort, page, page_size: 6, ...activeFilters })
      .then((result) => {
        if (!cancelled) {
          setJobs(result.items);
          setTotal(result.total);
          setTotalPages(result.total_pages);
        }
      })
      .catch((requestError) => {
        if (!cancelled) setError(requestError instanceof Error ? requestError.message : "공고를 불러오지 못했습니다.");
      });
    return () => { cancelled = true; };
  }, [activeFilters, page, query, sort]);

  async function openJob(job: Job) {
    try {
      setSelectedJob(await getJob(job.id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "공고 상세를 불러오지 못했습니다.");
    }
  }

  function updateFilter(name: string, value: string) {
    setPage(1);
    setActiveFilters((current) => ({ ...current, [name]: value }));
  }

  return (
    <main className="jobs-page">
      {previousBackground && <div className="dashboard-background dashboard-background-previous" style={{ backgroundImage: `url(${previousBackground})` }} aria-hidden="true" />}
      <div className={`dashboard-background dashboard-background-current ${previousBackground ? "is-transitioning" : ""}`} style={{ backgroundImage: `url(${displayBackground})` }} aria-hidden="true" />
      <section className="dashboard-hero">
        <nav className="dashboard-nav liquid-glass">
          <a className="dashboard-logo" href="#top">JOBDA</a>
          <div className="dashboard-nav-links"><a href="#jobs">공고</a><a href="#settings">내 조건</a><a href="#settings">관심기업</a><a href="#alerts">알림</a></div>
          <button className="dashboard-logout" onClick={onLogout}>로그아웃</button>
        </nav>
        <div className="dashboard-hero-content" id="top">
          <div className="dashboard-hero-main">
            <AnimatedHeading />
            <FadeIn delay={800}><p className="dashboard-subtitle">원하는 조건의 공고를 모으고, 다음 기회를 선명하게 준비하세요.</p></FadeIn>
            <FadeIn delay={1200} className="dashboard-actions"><a className="dashboard-primary-action" href="#jobs">공고 보기</a><a className="dashboard-secondary-action liquid-glass" href="#settings">내 조건 설정</a></FadeIn>
          </div>
          <FadeIn delay={1400} className="dashboard-tag"><div className="liquid-glass">맞춤 공고. 조건 저장. 알림.</div></FadeIn>
        </div>
      </section>
      <div className="jobs-shell">
      <section className="jobs-heading" id="jobs">
        <div><span className="section-kicker">OPEN ROLES</span><h1>공고를 찾아보세요.</h1><p>{total}개의 테스트 공고가 준비되어 있습니다.</p></div>
        <div className="source-note">사람인 · ALIO<br /><small>테스트 데이터 기반</small></div>
      </section>
      <section className="filter-bar" aria-label="공고 필터">
        <label className="filter-search"><span>검색</span><input aria-label="회사명 또는 공고명 검색" placeholder="회사명 또는 공고명 검색" value={query} onChange={(event) => { setPage(1); setQuery(event.target.value); }} /></label>
        <label className="filter-control"><span>정렬</span><select aria-label="정렬" value={sort} onChange={(event) => { setPage(1); setSort(event.target.value); }}><option value="latest">최신순</option><option value="deadline">마감임박순</option></select></label>
        {Object.entries(filters).map(([name, values]) => <label className="filter-control" key={name}><span>{name === "job_category" ? "직무" : name === "company_size" ? "기업규모" : name === "employment_type" ? "고용형태" : name === "experience" ? "경력" : "지역"}</span><select aria-label={name} value={activeFilters[name] ?? ""} onChange={(event) => updateFilter(name, event.target.value)}>{values.map((value) => <option key={value} value={value}>{value || "전체"}</option>)}</select></label>)}
      </section>
      {error && <p className="error page-error">{error}</p>}
      <section className="jobs-content">
        <div className="job-list">{jobs.map((job) => <button className="job-row" key={job.id} onClick={() => openJob(job)}><span className="job-source">{job.source}</span><span className="job-main"><strong>{job.company}</strong><b>{job.title}</b><small>{job.job_category} · {job.experience} · {job.location}</small></span><span className="job-meta"><strong>D-{Math.max(0, Math.ceil((new Date(`${job.deadline}T00:00:00`).getTime() - Date.now()) / 86400000))}</strong><small>{formatDeadline(job.deadline)}</small></span></button>)}</div>
        {selectedJob && <aside className="job-detail"><button className="close-button" onClick={() => setSelectedJob(null)} aria-label="상세 닫기">×</button><span className="section-kicker">{selectedJob.source} / 상세</span><h2>{selectedJob.title}</h2><p className="detail-company">{selectedJob.company}</p><div className="detail-grid"><span>직무<strong>{selectedJob.job_category}</strong></span><span>경력<strong>{selectedJob.experience}</strong></span><span>지역<strong>{selectedJob.location}</strong></span><span>고용형태<strong>{selectedJob.employment_type}</strong></span><span>기업규모<strong>{selectedJob.company_size}</strong></span><span>학력<strong>{selectedJob.education}</strong></span></div><p className="detail-description">{selectedJob.description}</p><a className="source-link" href={selectedJob.source_url} target="_blank" rel="noreferrer">원본 공고 보기 ↗</a></aside>}
      </section>
      <nav className="pagination" aria-label="공고 페이지"><button disabled={page === 1} onClick={() => setPage((current) => current - 1)}>이전</button><span>{page} / {totalPages}</span><button disabled={page === totalPages} onClick={() => setPage((current) => current + 1)}>다음</button></nav>
      <div id="settings"><PersonalizationPanel /></div>
      <div id="alerts"><PushPanel /></div>
      </div>
    </main>
  );
}

export default JobsPage;
