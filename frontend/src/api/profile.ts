import type { UserProfile } from "../types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const expectedBackendUrl = apiBaseUrl || "http://127.0.0.1:8010";

export class ProfileAPIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProfileAPIError";
  }
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      return body.detail;
    }
    return JSON.stringify(body.detail ?? body) ?? "后端返回错误";
  } catch {
    return `后端返回 ${response.status}`;
  }
}

export async function parseProfile(profileText: string): Promise<UserProfile> {
  if (!apiBaseUrl) {
    throw new ProfileAPIError("请先配置 VITE_API_BASE_URL");
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/profile/parse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ profile_text: profileText }),
    });

    if (!response.ok) {
      throw new ProfileAPIError(await readErrorMessage(response));
    }

    const body = (await response.json()) as { user_profile: UserProfile };
    return body.user_profile;
  } catch (error) {
    if (error instanceof ProfileAPIError) {
      throw error;
    }

    throw new ProfileAPIError(
      `无法连接后端服务，请确认 FastAPI 已运行在 ${expectedBackendUrl}`,
    );
  }
}
