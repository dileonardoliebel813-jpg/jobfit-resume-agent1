import type { JDProfile } from "../types";
import { getApiBaseUrl } from "./base";

export interface AnalyzeJDResponse {
  jd_profile: JDProfile;
}

export class JDAPIError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "JDAPIError";
    this.status = status;
  }
}

const apiBaseUrl = getApiBaseUrl();
const expectedBackendUrl = apiBaseUrl;

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      if (body.detail.startsWith("LLM API call failed")) {
        return body.detail;
      }
      return body.detail;
    }
    return JSON.stringify(body.detail ?? body) ?? "后端返回错误";
  } catch {
    return `后端返回 ${response.status}`;
  }
}

export async function analyzeJD(rawJD: string): Promise<AnalyzeJDResponse> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/jd/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ raw_jd: rawJD }),
    });

    if (!response.ok) {
      throw new JDAPIError(await readErrorMessage(response), response.status);
    }

    return (await response.json()) as AnalyzeJDResponse;
  } catch (error) {
    if (error instanceof JDAPIError) {
      throw error;
    }

    throw new JDAPIError(
      `无法连接后端服务，请确认 FastAPI 已运行在 ${expectedBackendUrl}`,
    );
  }
}
