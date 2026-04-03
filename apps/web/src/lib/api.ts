/**
 * Browser: empty NEXT_PUBLIC_API_URL → same-origin (e.g. nginx on 443 proxying /api/).
 * Server (SSR): INTERNAL_API_URL or public URL; Docker uses http://api:8000.
 */
function apiBase(): string {
  const p = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (typeof window !== "undefined") {
    if (!p) return "";
    return p.replace(/\/$/, "");
  }
  const internal = process.env.INTERNAL_API_URL?.trim();
  if (internal) return internal.replace(/\/$/, "");
  if (p) return p.replace(/\/$/, "");
  return "http://localhost:8000";
}

export function apiUrl(path: string): string {
  const suffix = path.startsWith("/") ? path : `/${path}`;
  const base = apiBase();
  if (base === "") return suffix;
  return `${base}${suffix}`;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit & { token?: string | null }
): Promise<T> {
  const { token, ...init } = options || {};
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(apiUrl(path), { ...init, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json() as Promise<T>;
}
