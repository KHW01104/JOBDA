import { FormEvent, useEffect, useState } from "react";

import { CompanyWatch, createFilter, createScrap, createWatch, deleteFilter, deleteScrap, deleteWatch, getFilters, getScraps, getWatches, JobScrap, UserFilter } from "../../api/client";

function PersonalizationPanel() {
  const [filters, setFilters] = useState<UserFilter[]>([]);
  const [watches, setWatches] = useState<CompanyWatch[]>([]);
  const [scraps, setScraps] = useState<JobScrap[]>([]);
  const [filterName, setFilterName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobId, setJobId] = useState("1");
  const [error, setError] = useState("");

  async function refresh() {
    const [nextFilters, nextWatches, nextScraps] = await Promise.all([getFilters(), getWatches(), getScraps()]);
    setFilters(nextFilters); setWatches(nextWatches); setScraps(nextScraps);
  }

  useEffect(() => { refresh().catch(() => setError("개인화 데이터를 불러오지 못했습니다.")); }, []);

  async function submit(event: FormEvent, action: () => Promise<unknown>, reset: () => void) {
    event.preventDefault(); setError("");
    try { await action(); reset(); await refresh(); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "저장하지 못했습니다."); }
  }

  return <section className="personalization-panel">
    <div className="panel-heading"><span className="section-kicker">MY SETTINGS</span><h2>내 조건과 저장 목록</h2></div>
    {error && <p className="error">{error}</p>}
    <div className="personalization-grid">
      <div><h3>내 조건</h3><form onSubmit={(event) => submit(event, () => createFilter(filterName), () => setFilterName(""))}><input aria-label="필터 이름" placeholder="필터 이름" value={filterName} onChange={(event) => setFilterName(event.target.value)} required /><button type="submit">조건 저장</button></form><ul>{filters.map((item) => <li key={item.id}><span>{item.name}</span><button className="icon-button" onClick={() => deleteFilter(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
      <div><h3>관심기업</h3><form onSubmit={(event) => submit(event, () => createWatch(companyName), () => setCompanyName(""))}><input aria-label="관심기업 이름" placeholder="기업명" value={companyName} onChange={(event) => setCompanyName(event.target.value)} required /><button type="submit">기업 추가</button></form><ul>{watches.map((item) => <li key={item.id}><span>{item.company_name}</span><button className="icon-button" onClick={() => deleteWatch(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
      <div><h3>스크랩</h3><form onSubmit={(event) => submit(event, () => createScrap(Number(jobId)), () => setJobId("1"))}><input aria-label="스크랩 공고 번호" type="number" min="1" placeholder="공고 번호" value={jobId} onChange={(event) => setJobId(event.target.value)} required /><button type="submit">공고 저장</button></form><ul>{scraps.map((item) => <li key={item.id}><span>공고 #{item.job_id}</span><button className="icon-button" onClick={() => deleteScrap(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
    </div>
  </section>;
}

export default PersonalizationPanel;