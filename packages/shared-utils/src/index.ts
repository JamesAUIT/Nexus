// Shared utilities (formatters, API helpers)
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}
