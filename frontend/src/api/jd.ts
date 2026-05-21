import type { JDProfile } from "../types";

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

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const expectedBackendUrl = apiBaseUrl || "http://127.0.0.1:8010";

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
  if (!apiBaseUrl) {
    throw new JDAPIError("请先配置 VITE_API_BASE_URL");
  }

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
