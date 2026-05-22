import type {
  ATSReviewResult,
  FactCheckResult,
  JDProfile,
  MatchAnalysis,
  GenerationRecommendation,
  ResumeJSON,
  UserProfile,
} from "../types";
import { getApiBaseUrl } from "./base";

const apiBaseUrl = getApiBaseUrl();
const expectedBackendUrl = apiBaseUrl;

export interface EvidenceItem {
  requirement: string;
  matched_experience: string;
  evidence_snippet: string;
  confidence: number;
}

export interface ResumeGenerateResult {
  resume_json: ResumeJSON;
  match: MatchAnalysis;
  evidence: EvidenceItem[];
  strategy_notes: string[];
  coverage_score: number;
  missing_fields: string[];
  generation_recommendation: GenerationRecommendation;
}

export class ResumeAPIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ResumeAPIError";
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

async function postJSON<T>(path: string, payload: unknown): Promise<T> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new ResumeAPIError(await readErrorMessage(response));
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ResumeAPIError) {
      throw error;
    }

    throw new ResumeAPIError(
      `无法连接后端服务，请确认 FastAPI 已运行在 ${expectedBackendUrl}`,
    );
  }
}

export async function generateResume(
  jdProfile: JDProfile,
  userProfile: UserProfile,
): Promise<ResumeGenerateResult> {
  return postJSON<ResumeGenerateResult>("/api/v1/resume/generate", {
    jd_profile: jdProfile,
    user_profile: userProfile,
  });
}

export async function reviewATS(
  resume: ResumeJSON,
  jdProfile: JDProfile,
): Promise<ATSReviewResult> {
  const body = await postJSON<{ ats_review: ATSReviewResult }>("/api/v1/resume/ats-review", {
    resume_json: resume,
    jd_profile: jdProfile,
  });
  return body.ats_review;
}

export async function factCheckResume(
  resume: ResumeJSON,
  userProfile: UserProfile,
): Promise<FactCheckResult> {
  const body = await postJSON<{ fact_check: FactCheckResult }>("/api/v1/resume/fact-check", {
    resume_json: resume,
    user_profile: userProfile,
  });
  return body.fact_check;
}
