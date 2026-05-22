import type { JDProfile, MatchDiagnoseResult, UserProfile } from "../types";
import { getApiBaseUrl } from "./base";

const apiBaseUrl = getApiBaseUrl();
const expectedBackendUrl = apiBaseUrl;

export class MatchAPIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MatchAPIError";
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

export async function diagnoseMatch(
  jdProfile: JDProfile,
  userProfile: UserProfile,
  rawProfileText: string,
  userConfirmedAbsentRequirements: string[],
): Promise<MatchDiagnoseResult> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/match/diagnose`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        jd_profile: jdProfile,
        user_profile: userProfile,
        raw_profile_text: rawProfileText,
        user_confirmed_absent_requirements: userConfirmedAbsentRequirements,
      }),
    });

    if (!response.ok) {
      throw new MatchAPIError(await readErrorMessage(response));
    }

    return (await response.json()) as MatchDiagnoseResult;
  } catch (error) {
    if (error instanceof MatchAPIError) {
      throw error;
    }

    throw new MatchAPIError(
      `无法连接后端服务，请确认 FastAPI 已运行在 ${expectedBackendUrl}`,
    );
  }
}
