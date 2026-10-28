let csrf = '';
export function setCSRF(value: string) {
  csrf = value;
}
export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || 'GET';
  const headers = new Headers(options.headers);
  if (!['GET', 'HEAD'].includes(method)) headers.set('X-CSRF-Token', csrf);
  if (options.body && !(options.body instanceof FormData))
    headers.set('Content-Type', 'application/json');
  const response = await fetch('/api' + path, { ...options, headers, credentials: 'same-origin' });
  if (!response.ok) {
    if (response.status === 401 && !path.includes('/auth/login'))
      window.dispatchEvent(new Event('messi-session-expired'));
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = `Request failed (${response.status})`;
    }
    if (Array.isArray(detail))
      detail = detail.map((x: any) => x.msg || JSON.stringify(x)).join('; ');
    if (typeof detail !== 'string') detail = JSON.stringify(detail);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}
export const post = <T = any>(path: string, body: unknown = {}) =>
  api<T>(path, { method: 'POST', body: JSON.stringify(body) });
export const number = (n: number | undefined, digits = 0) =>
  new Intl.NumberFormat('en-AU', { maximumFractionDigits: digits }).format(n || 0);
