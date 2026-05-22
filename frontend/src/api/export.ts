import type { ResumeContactInfo, ResumeJSON } from "../types";
import { getApiBaseUrl } from "./base";

const apiBaseUrl = getApiBaseUrl();
const expectedBackendUrl = apiBaseUrl;

export class ExportAPIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExportAPIError";
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

export async function exportResumePDF(
  resume: ResumeJSON,
  contactInfo?: ResumeContactInfo,
): Promise<Blob> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/export/resume`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        resume_json: resume,
        format: "pdf",
        layout: "one_page",
        photo_mode: "placeholder",
        contact_info: contactInfo,
      }),
    });

    if (!response.ok) {
      throw new ExportAPIError(await readErrorMessage(response));
    }

    return await response.blob();
  } catch (error) {
    if (error instanceof ExportAPIError) {
      throw error;
    }

    throw new ExportAPIError(
      `无法连接后端服务，请确认 FastAPI 已运行在 ${expectedBackendUrl}`,
    );
  }
}
