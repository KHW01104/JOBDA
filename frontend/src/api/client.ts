const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type User = {
  id: number;
  username: string;
  display_name: string;
  role: "ADMIN" | "USER";
  is_active: boolean;
  must_change_password: boolean;
};

export type Job = {
  id: number;
  company: string;
  title: string;
  job_category: string;
  location: string;
  experience: string;
  employment_type: string;
  company_size: string;
  deadline: string;
  source: string;
  source_url: string;
  status: string;
};

export type JobDetail = Job & {
  education: string;
  description: string;
  published_at: string;
};

export type JobListResponse = {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type UserFilter = { id: number; name: string; job_categories: string[]; is_active: boolean };
export type CompanyWatch = { id: number; company_name: string; company_id: number | null };
export type JobScrap = { id: number; job_id: number; status: string; memo: string | null };
export type PushSubscription = { id: number; endpoint: string; p256dh: string; auth: string; user_agent: string | null };
export type NotificationEvent = { id: number; type: string; job_id: number | null; title: string; body: string; is_read: boolean; created_at: string };

type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("jobda_access_token");
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "요청을 처리하지 못했습니다.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function login(username: string, password: string) {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function createUser(username: string, password: string, displayName: string) {
  return request<User>("/api/admin/users", {
    method: "POST",
    body: JSON.stringify({ username, password, display_name: displayName }),
  });
}

export function getJobs(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return request<JobListResponse>(`/api/jobs?${query.toString()}`);
}

export function getJob(id: number) {
  return request<JobDetail>(`/api/jobs/${id}`);
}

export function getFilters() { return request<UserFilter[]>("/api/personalization/filters"); }
export function createFilter(name: string) { return request<UserFilter>("/api/personalization/filters", { method: "POST", body: JSON.stringify({ name, job_categories: [] }) }); }
export function deleteFilter(id: number) { return request<void>(`/api/personalization/filters/${id}`, { method: "DELETE" }); }
export function getWatches() { return request<CompanyWatch[]>("/api/personalization/watches"); }
export function createWatch(companyName: string) { return request<CompanyWatch>("/api/personalization/watches", { method: "POST", body: JSON.stringify({ company_name: companyName }) }); }
export function deleteWatch(id: number) { return request<void>(`/api/personalization/watches/${id}`, { method: "DELETE" }); }
export function getScraps() { return request<JobScrap[]>("/api/personalization/scraps"); }
export function createScrap(jobId: number) { return request<JobScrap>("/api/personalization/scraps", { method: "POST", body: JSON.stringify({ job_id: jobId }) }); }
export function deleteScrap(id: number) { return request<void>(`/api/personalization/scraps/${id}`, { method: "DELETE" }); }
export function createPushSubscription(subscription: { endpoint: string; p256dh: string; auth: string; user_agent: string }) { return request<PushSubscription>("/api/notifications/subscriptions", { method: "POST", body: JSON.stringify(subscription) }); }
export function getPushSubscriptions() { return request<PushSubscription[]>("/api/notifications/subscriptions"); }
export function deletePushSubscription(id: number) { return request<void>(`/api/notifications/subscriptions/${id}`, { method: "DELETE" }); }
export function getNotificationEvents() { return request<NotificationEvent[]>("/api/notifications/events"); }
