const defaultLocalApiBaseUrl = "http://127.0.0.1:8010";

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

function isPrivateOrLocalHost(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "0.0.0.0" ||
    hostname.startsWith("127.") ||
    hostname.startsWith("10.") ||
    hostname.startsWith("192.168.") ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
  );
}

export function getApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
  const browserOrigin =
    typeof window !== "undefined" ? window.location.origin.replace(/\/$/, "") : "";

  if (!envUrl) {
    return browserOrigin || defaultLocalApiBaseUrl;
  }

  const envHost = hostnameOf(envUrl);
  const currentHost = typeof window !== "undefined" ? window.location.hostname : "";

  if (
    browserOrigin &&
    currentHost &&
    !isPrivateOrLocalHost(currentHost) &&
    isPrivateOrLocalHost(envHost)
  ) {
    return browserOrigin;
  }

  return envUrl;
}
