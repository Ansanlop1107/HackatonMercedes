export async function apiFetch(url, options = {}) {
  const mergedHeaders = {
    'ngrok-skip-browser-warning': 'true',
    ...(options.headers || {})
  };

  return fetch(url, {
    ...options,
    headers: mergedHeaders
  });
}
