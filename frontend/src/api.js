
function getCookie(name) {
  const cookies = document.cookie.split(";");

  for (const cookie of cookies) {
    const [key, ...value] = cookie.trim().split("=");

    if (key === name) {
      return decodeURIComponent(value.join("="));
    }
  }

  return "";
}

export async function apiRequest(url, method = "GET", data = null) {
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);

  if (unsafe && !getCookie("csrftoken")) {
    await fetch("/api/auth/csrf/", {
      credentials: "same-origin",
    });
  }

  const response = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(unsafe ? { "X-CSRFToken": getCookie("csrftoken") } : {}),
      ...(data !== null ? { "Content-Type": "application/json" } : {}),
    },
    ...(data !== null ? { body: JSON.stringify(data) } : {}),
  });

  const text = await response.text();
  let result = {};

  try {
    result = text ? JSON.parse(text) : {};
  } catch {
    result = { detail: text.slice(0, 300) };
  }

  if (!response.ok) {
    const message =
      result.detail ||
      result.error ||
      result.message ||
      JSON.stringify(result);

    throw new Error(`${response.status}: ${message}`);
  }

  return result;
}
