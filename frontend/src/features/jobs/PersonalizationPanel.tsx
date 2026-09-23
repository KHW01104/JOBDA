import { FormEvent, useEffect, useState } from "react";

import { CompanyWatch, createFilter, createScrap, createWatch, deleteFilter, deleteScrap, deleteWatch, getFilters, getScraps, getWatches, JobScrap, UserFilter } from "../../api/client";

const values = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);
const optionalNumber = (value: string) => value.trim() === "" ? null : Number(value);

function PersonalizationPanel() {
  const [filters, setFilters] = useState<UserFilter[]>([]);
  const [watches, setWatches] = useState<CompanyWatch[]>([]);
  const [scraps, setScraps] = useState<JobScrap[]>([]);
  const [filterName, setFilterName] = useState("");
  const [includedKeywords, setIncludedKeywords] = useState("");
  const [excludedKeywords, setExcludedKeywords] = useState("");
  const [locations, setLocations] = useState("");
  const [employmentTypes, setEmploymentTypes] = useState("");
  const [jobCategories, setJobCategories] = useState("");
  const [companySizes, setCompanySizes] = useState("");
  const [experienceMin, setExperienceMin] = useState("");
  const [experienceMax, setExperienceMax] = useState("");
  const [minimumEmployeeCount, setMinimumEmployeeCount] = useState("");
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
      <div><h3>공고 저장 조건</h3><p className="hint">저장한 조건에 맞는 공고만 수집해 내 목록에 추가합니다.</p><form onSubmit={(event) => submit(event, () => createFilter({ name: filterName, included_keywords: values(includedKeywords), excluded_keywords: values(excludedKeywords), locations: values(locations), employment_types: values(employmentTypes), job_categories: values(jobCategories), company_sizes: values(companySizes), experience_min: optionalNumber(experienceMin), experience_max: optionalNumber(experienceMax), minimum_employee_count: optionalNumber(minimumEmployeeCount), is_active: true }), () => { setFilterName(""); setIncludedKeywords(""); setExcludedKeywords(""); setLocations(""); setEmploymentTypes(""); setJobCategories(""); setCompanySizes(""); setExperienceMin(""); setExperienceMax(""); setMinimumEmployeeCount(""); })}><input aria-label="필터 이름" placeholder="예: 개발 직무" value={filterName} onChange={(event) => setFilterName(event.target.value)} required /><input aria-label="포함 키워드" placeholder="포함 키워드 (예: 개발,백엔드)" value={includedKeywords} onChange={(event) => setIncludedKeywords(event.target.value)} /><input aria-label="제외 키워드" placeholder="제외 키워드 (예: 인턴,계약직)" value={excludedKeywords} onChange={(event) => setExcludedKeywords(event.target.value)} /><input aria-label="직무 분류" placeholder="직무 분류 (예: Backend,전기)" value={jobCategories} onChange={(event) => setJobCategories(event.target.value)} /><input aria-label="희망 지역" placeholder="희망 지역 (예: 서울,경기)" value={locations} onChange={(event) => setLocations(event.target.value)} /><input aria-label="고용 형태" placeholder="고용 형태 (예: 정규직)" value={employmentTypes} onChange={(event) => setEmploymentTypes(event.target.value)} /><input aria-label="기업 규모" placeholder="기업 규모 (예: 중소,공공기관)" value={companySizes} onChange={(event) => setCompanySizes(event.target.value)} /><div className="condition-number-inputs"><label>최소 경력(년)<input aria-label="최소 경력" type="number" min="0" value={experienceMin} onChange={(event) => setExperienceMin(event.target.value)} /></label><label>최대 경력(년)<input aria-label="최대 경력" type="number" min="0" value={experienceMax} onChange={(event) => setExperienceMax(event.target.value)} /></label></div><input aria-label="최소 직원 수" type="number" min="1" placeholder="최소 직원 수" value={minimumEmployeeCount} onChange={(event) => setMinimumEmployeeCount(event.target.value)} /><button type="submit">조건 저장</button></form><ul>{filters.map((item) => <li key={item.id}><span>{item.name}<small>{[...item.included_keywords, ...item.job_categories, ...item.locations].join(", ") || "전체 공고"}</small></span><button className="icon-button" onClick={() => deleteFilter(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
      <div><h3>관심기업</h3><form onSubmit={(event) => submit(event, () => createWatch(companyName), () => setCompanyName(""))}><input aria-label="관심기업 이름" placeholder="기업명" value={companyName} onChange={(event) => setCompanyName(event.target.value)} required /><button type="submit">기업 추가</button></form><ul>{watches.map((item) => <li key={item.id}><span>{item.company_name}</span><button className="icon-button" onClick={() => deleteWatch(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
      <div><h3>스크랩</h3><form onSubmit={(event) => submit(event, () => createScrap(Number(jobId)), () => setJobId("1"))}><input aria-label="스크랩 공고 번호" type="number" min="1" placeholder="공고 번호" value={jobId} onChange={(event) => setJobId(event.target.value)} required /><button type="submit">공고 저장</button></form><ul>{scraps.map((item) => <li key={item.id}><span>공고 #{item.job_id}</span><button className="icon-button" onClick={() => deleteScrap(item.id).then(refresh)}>삭제</button></li>)}</ul></div>
    </div>
  </section>;
}

export default PersonalizationPanel;
