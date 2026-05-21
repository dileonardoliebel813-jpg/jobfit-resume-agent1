export type Severity = "low" | "medium" | "high";

export interface ResumeStrategy {
  must_highlight: string[];
  should_weaken: string[];
  tone: string;
}

export interface JDProfile {
  position: string;
  job_level: string;
  job_type: string;
  hard_requirements: string[];
  core_tasks: string[];
  required_skills: string[];
  preferred_experience: string[];
  hidden_preferences: string[];
  resume_strategy: ResumeStrategy;
}

export interface WorkExperience {
  company: string;
  role: string;
  duration: string;
  highlights: string[];
  skills: string[];
}

export interface UserProfile {
  name: string;
  headline: string;
  skills: string[];
  experiences: WorkExperience[];
  education: string[];
}

export interface ResumeContactInfo {
  name: string;
  age: string;
  phone: string;
  email: string;
  location: string;
  github: string;
  target_title: string;
}

export interface SkillMatch {
  skill: string;
  score: number;
  evidence: string;
}

export interface MatchAnalysis {
  overall_score: number;
  matched_skills: SkillMatch[];
  gaps: string[];
  recommendations: string[];
}

export type EvidenceStatus =
  | "direct_evidence"
  | "weak_evidence"
  | "missing_evidence"
  | "user_confirmed_absent";

export type GenerationRecommendation = "ready" | "needs_more_info" | "not_recommended";

export interface EvidenceDiagnosisItem {
  requirement: string;
  category: string;
  status: EvidenceStatus;
  matched_experience: string;
  evidence_snippet: string;
  confidence: number;
  suggestion: string;
}

export interface MissingEvidenceQuestion {
  requirement: string;
  question: string;
  reason: string;
}

export interface SafeResumeStrategy {
  can_write: string[];
  should_weaken: string[];
  must_not_claim: string[];
}

export interface MatchDiagnoseResult {
  coverage_score: number;
  generation_recommendation: GenerationRecommendation;
  evidence_items: EvidenceDiagnosisItem[];
  missing_evidence_questions: MissingEvidenceQuestion[];
  safe_resume_strategy: SafeResumeStrategy;
}

export type ResumeEvidenceStatus =
  | "supported"
  | "transferable"
  | "inferred"
  | "unsupported"
  | "missing";

export type ResumeRiskLevel = "low" | "medium" | "high";

export interface ResumeBullet {
  text: string;
  evidence_status: ResumeEvidenceStatus;
  risk_level: ResumeRiskLevel;
}

export interface ResumeModule {
  title: string;
  subtitle: string;
  bullets: ResumeBullet[];
}

export interface ResumeSideReport {
  missing_info: string[];
  weak_match_points: string[];
  suggested_user_inputs: string[];
  assumptions_need_confirmation: string[];
  match_gap_summary: string;
}

export interface ResumeJSON {
  candidate_name: string;
  target_title: string;
  headline: string;
  summary: ResumeBullet[];
  skills: string[];
  projects: ResumeModule[];
  practice_experiences: ResumeModule[];
  campus_or_competition: ResumeModule[];
  education: string[];
  self_evaluation: ResumeBullet[];
  side_report: ResumeSideReport;
}

export interface ATSIssue {
  category: string;
  severity: Severity;
  message: string;
  suggestion: string;
}

export interface ATSReviewResult {
  score: number;
  keyword_coverage: number;
  summary: string;
  issues: ATSIssue[];
}

export interface FactCheckItem {
  claim: string;
  status: ResumeEvidenceStatus;
  source_hint: string;
  note: string;
}

export interface FactCheckResult {
  risk_level: Severity;
  summary: string;
  items: FactCheckItem[];
}
