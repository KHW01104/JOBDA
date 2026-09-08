import { useEffect, useState } from "react";

import { getJob, getJobs, Job, JobDetail, User } from "../../api/client";
import PersonalizationPanel from "./PersonalizationPanel";

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

function formatDeadline(deadline: string) {
  return deadline.replaceAll("-", ".").slice(5);
}

function JobsPage({ user, onLogout }: JobsPageProps) {
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
    <main className="jobs-shell">
      <header className="topbar">
        <div><span className="eyebrow">JOBDA / PHASE 3</span><strong>채용공고 탐색</strong></div>
        <div className="user-menu"><span>{user.display_name} · {user.role}</span><button className="text-button" onClick={onLogout}>로그아웃</button></div>
      </header>
      <section className="jobs-heading">
        <div><span className="section-kicker">OPEN ROLES</span><h1>공고를 찾아보세요.</h1><p>{total}개의 테스트 공고가 준비되어 있습니다.</p></div>
        <div className="source-note">사람인 · ALIO<br /><small>테스트 데이터 기반</small></div>
      </section>
      <section className="filter-bar">
        <input aria-label="회사명 또는 공고명 검색" placeholder="회사명 또는 공고명 검색" value={query} onChange={(event) => { setPage(1); setQuery(event.target.value); }} />
        <select aria-label="정렬" value={sort} onChange={(event) => { setPage(1); setSort(event.target.value); }}><option value="latest">최신순</option><option value="deadline">마감임박순</option></select>
        {Object.entries(filters).map(([name, values]) => <select aria-label={name} key={name} value={activeFilters[name] ?? ""} onChange={(event) => updateFilter(name, event.target.value)}>{values.map((value) => <option key={value} value={value}>{value || name.replace("_", " ")}</option>)}</select>)}
      </section>
      {error && <p className="error page-error">{error}</p>}
      <section className="jobs-content">
        <div className="job-list">{jobs.map((job) => <button className="job-row" key={job.id} onClick={() => openJob(job)}><span className="job-source">{job.source}</span><span className="job-main"><strong>{job.company}</strong><b>{job.title}</b><small>{job.job_category} · {job.experience} · {job.location}</small></span><span className="job-meta"><strong>D-{Math.max(0, Math.ceil((new Date(`${job.deadline}T00:00:00`).getTime() - Date.now()) / 86400000))}</strong><small>{formatDeadline(job.deadline)}</small></span></button>)}</div>
        {selectedJob && <aside className="job-detail"><button className="close-button" onClick={() => setSelectedJob(null)} aria-label="상세 닫기">×</button><span className="section-kicker">{selectedJob.source} / 상세</span><h2>{selectedJob.title}</h2><p className="detail-company">{selectedJob.company}</p><div className="detail-grid"><span>직무<strong>{selectedJob.job_category}</strong></span><span>경력<strong>{selectedJob.experience}</strong></span><span>지역<strong>{selectedJob.location}</strong></span><span>고용형태<strong>{selectedJob.employment_type}</strong></span><span>기업규모<strong>{selectedJob.company_size}</strong></span><span>학력<strong>{selectedJob.education}</strong></span></div><p className="detail-description">{selectedJob.description}</p><a className="source-link" href={selectedJob.source_url} target="_blank" rel="noreferrer">원본 공고 보기 ↗</a></aside>}
      </section>
      <nav className="pagination" aria-label="공고 페이지"><button disabled={page === 1} onClick={() => setPage((current) => current - 1)}>이전</button><span>{page} / {totalPages}</span><button disabled={page === totalPages} onClick={() => setPage((current) => current + 1)}>다음</button></nav>
      <PersonalizationPanel />
    </main>
  );
}

export default JobsPage;
