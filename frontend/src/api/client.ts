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
