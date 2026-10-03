const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {

  const headers = new Headers(options.headers);

  // Only send JSON Content-Type when we actually have a body.
  // This avoids unnecessary CORS preflight requests for GET calls.
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {

    const errorText = await response.text();

    throw new Error(
      errorText ||
      `KAVRON API error: ${response.status}`
    );
  }

  return response.json() as Promise<T>;
}