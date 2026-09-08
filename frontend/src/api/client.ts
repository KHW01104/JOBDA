const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type User = {
  id: number;
  username: string;
  display_name: string;
  role: "ADMIN" | "USER";
  is_active: boolean;
  must_change_password: boolean;
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
