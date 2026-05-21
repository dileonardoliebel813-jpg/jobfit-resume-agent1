import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  FileText,
  History,
  Loader2,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";

import { analyzeJD } from "../api/jd";
import { diagnoseMatch } from "../api/match";
import {
  type ResumeGenerateResult,
  factCheckResume,
  generateResume,
  reviewATS,
} from "../api/resume";
import ExportButton from "../components/ExportButton";
import ResumePreview from "../components/ResumePreview";
import type {
  ATSReviewResult,
  FactCheckResult,
  JDProfile,
  MatchDiagnoseResult,
  ResumeContactInfo,
  UserProfile,
} from "../types";

type WizardStep = 1 | 2 | 3 | 4 | 5;

type SideView = "workflow" | "history";

interface ExperienceForm {
  education: string;
  skills: string;
  project: string;
  campus: string;
}

interface ResumeHistoryItem {
  id: string;
  createdAt: string;
  candidateName: string;
  targetTitle: string;
  jdPosition: string;
  coverageScore: number;
  contactInfo: ResumeContactInfo;
  resumeResult: ResumeGenerateResult;
}

interface CompletionSuggestion {
  title: string;
  detail: string;
  target: keyof ExperienceForm;
  template: string;
}

const historyStorageKey = "jobfit_resume_history_v1";

const emptyContact: ResumeContactInfo = {
  name: "",
  age: "",
  phone: "",
  email: "",
  location: "",
  github: "",
  target_title: "AI 产品经理",
};

const emptyExperience: ExperienceForm = {
  education: "",
  skills: "",
  project: "",
  campus: "",
};

const exampleJD = `AI 产品经理
岗位职责：
1. 负责 AI 产品需求分析、PRD 撰写、原型设计和版本迭代。
2. 调研用户痛点与竞品方案，结合大模型能力设计产品功能。
3. 协同算法、研发、测试、运营团队推动项目落地。
4. 建立数据指标，跟踪产品效果并持续优化。

任职要求：
1. 熟悉产品设计流程，有 PRD、原型或需求分析经验。
2. 理解大模型、Prompt、RAG 或推荐系统相关概念。
3. 具备数据分析意识，能围绕指标做产品判断。
4. 有良好的沟通协作和项目推进能力。`;

const exampleContact: ResumeContactInfo = {
  name: "示例用户",
  age: "22岁",
  phone: "请替换为真实手机号",
  email: "example@email.com",
  location: "请填写城市",
  github: "https://github.com/example-user",
  target_title: "AI 产品经理",
};

const exampleExperience: ExperienceForm = {
  education:
    "某高校 | 某专业 | 本科 | 2022.09 - 2026.06\n主修课程：产品设计、数据分析、Python 程序设计、数据库基础\n奖项或荣誉：请替换为你真实获得的奖项",
  skills:
    "Python、SQL、Excel、Figma、Axure、XMind、PRD、需求分析、竞品分析、AI 辅助开发、数据清洗、产品原型设计",
  project:
    "AI 学习计划助手项目\n面向学生学习计划制定场景，梳理目标、时间、课程难度和复习周期等决策因素。\n使用 Figma / Axure 设计核心页面原型，整理任务拆解、计划推荐和进度反馈流程。\n结合 Python / SQL 做基础数据整理，尝试用 AI 工具辅助需求拆解和文档整理。\n请把以上内容替换为你真实做过的项目。",
  campus:
    "课程设计或竞赛经历：请填写真实比赛、课程项目、调研报告或学生工作。\n团队协作经历：请填写你真实参与的沟通、文档、组织或复盘工作。",
};

const steps: Array<{ step: WizardStep; title: string; hint: string }> = [
  { step: 1, title: "岗位 JD", hint: "粘贴并分析" },
  { step: 2, title: "个人信息", hint: "姓名和联系方式" },
  { step: 3, title: "真实经历", hint: "教育、技能、项目" },
  { step: 4, title: "匹配确认", hint: "看覆盖率" },
  { step: 5, title: "简历导出", hint: "预览和 PDF" },
];

function splitList(value: string): string[] {
  return value
    .split(/[\n,，;；、/]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitLines(value: string): string[] {
  return value
    .split(/\n+/)
    .map((item) => item.trim().replace(/^[•*-]\s*/, ""))
    .filter(Boolean);
}

function composeProfileText(contact: ResumeContactInfo, form: ExperienceForm): string {
  return [
    contact.name && `姓名：${contact.name}`,
    contact.target_title && `目标岗位：${contact.target_title}`,
    contact.age && `年龄：${contact.age}`,
    contact.phone && `电话：${contact.phone}`,
    contact.email && `邮箱：${contact.email}`,
    contact.location && `所在地：${contact.location}`,
    contact.github && `GitHub：${contact.github}`,
    form.education && `教育背景：\n${form.education}`,
    form.skills && `专业技能：\n${form.skills}`,
    form.project && `项目经历：\n${form.project}`,
    form.campus && `校园 / 竞赛经历：\n${form.campus}`,
  ]
    .filter(Boolean)
    .join("\n\n");
}

function buildUserProfile(contact: ResumeContactInfo, form: ExperienceForm): UserProfile {
  const skills = Array.from(new Set(splitList(form.skills)));
  const projectLines = splitLines(form.project);
  const campusLines = splitLines(form.campus);
  const highlights = [...projectLines, ...campusLines].slice(0, 12);
  const firstProjectLine = projectLines[0] ?? "";

  return {
    name: contact.name.trim(),
    headline: contact.target_title.trim(),
    skills,
    experiences: highlights.length
      ? [
          {
            company: "",
            role: firstProjectLine || "项目实践",
            duration: "",
            highlights,
            skills: skills.filter((skill) => form.project.includes(skill)).slice(0, 10),
          },
        ]
      : [],
    education: splitLines(form.education),
  };
}

function isLowMatch(diagnosis: MatchDiagnoseResult | null): boolean {
  return Boolean(diagnosis && diagnosis.coverage_score < 0.35);
}

function readResumeHistory(): ResumeHistoryItem[] {
  try {
    const raw = window.localStorage.getItem(historyStorageKey);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as ResumeHistoryItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeResumeHistory(items: ResumeHistoryItem[]) {
  window.localStorage.setItem(historyStorageKey, JSON.stringify(items.slice(0, 12)));
}

function buildCompletionSuggestions(diagnosis: MatchDiagnoseResult | null): CompletionSuggestion[] {
  if (!diagnosis) {
    return [];
  }

  const questions = diagnosis.missing_evidence_questions.slice(0, 6);
  if (!questions.length) {
    return [];
  }

  return questions.map((item) => {
    const requirement = item.requirement;
    const isSkill = /技能|工具|SQL|Python|数据|原型|PRD|Prompt|AI|模型|分析/.test(requirement);
    const isCampus = /沟通|协作|竞赛|课程|组织|表达|推进|复盘/.test(requirement);
    const target: keyof ExperienceForm = isSkill ? "skills" : isCampus ? "campus" : "project";
    return {
      title: requirement,
      detail: item.question,
      target,
      template:
        target === "skills"
          ? `\n${requirement}：请填写你真实掌握的工具、课程训练或项目使用场景。`
          : target === "campus"
            ? `\n围绕“${requirement}”：请补充一个真实课程、竞赛、学生工作或团队协作经历，说明你做了什么、产出了什么。`
            : `\n围绕“${requirement}”：请补充一个真实项目片段，例如用户场景、需求拆解、原型设计、数据整理、协作对象或产出物。`,
    };
  });
}

function StepButton({
  step,
  activeStep,
  completed,
  onClick,
}: {
  step: (typeof steps)[number];
  activeStep: WizardStep;
  completed: boolean;
  onClick: () => void;
}) {
  const active = step.step === activeStep;
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left transition ${
        active
          ? "border-action bg-teal-50 text-slate-950"
          : completed
            ? "border-teal-100 bg-white text-slate-800"
            : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
      }`}
    >
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
          completed ? "bg-action text-white" : active ? "bg-white text-action" : "bg-slate-100"
        }`}
      >
        {completed ? <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> : step.step}
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-bold">{step.title}</span>
        <span className="mt-0.5 block truncate text-xs opacity-70">{step.hint}</span>
      </span>
    </button>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  rows,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  rows: number;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-slate-900">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        placeholder={placeholder}
        className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-800 outline-none transition focus:border-action focus:bg-white focus:ring-4 focus:ring-teal-50"
      />
    </label>
  );
}

function ContactInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-slate-900">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-2 h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-800 outline-none transition focus:border-action focus:bg-white focus:ring-4 focus:ring-teal-50"
      />
    </label>
  );
}

function PrimaryButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-action px-5 text-sm font-bold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-300"
    >
      {children}
    </button>
  );
}

function SecondaryButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-sm font-bold text-slate-700 transition hover:border-action hover:text-action disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
    >
      {children}
    </button>
  );
}

function LowMatchModal({
  onClose,
  onContinue,
}: {
  onClose: () => void;
  onContinue: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
              <AlertTriangle className="h-5 w-5" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-bold text-slate-950">当前信息与岗位匹配度不高</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <p className="mt-4 text-sm leading-7 text-slate-700">
          建议继续补充与岗位相关的真实项目、课程、竞赛或实践经历。你也可以继续生成简历，系统只会使用已提供的真实信息。
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <SecondaryButton onClick={onClose}>返回补充信息</SecondaryButton>
          <PrimaryButton onClick={onContinue}>继续生成简历</PrimaryButton>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [activeStep, setActiveStep] = useState<WizardStep>(1);
  const [sideView, setSideView] = useState<SideView>("workflow");
  const [rawJD, setRawJD] = useState("");
  const [contactInfo, setContactInfo] = useState<ResumeContactInfo>(emptyContact);
  const [experienceForm, setExperienceForm] = useState<ExperienceForm>(emptyExperience);
  const [jdProfile, setJDProfile] = useState<JDProfile | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [diagnosis, setDiagnosis] = useState<MatchDiagnoseResult | null>(null);
  const [resumeResult, setResumeResult] = useState<ResumeGenerateResult | null>(null);
  const [atsReview, setATSReview] = useState<ATSReviewResult | null>(null);
  const [factCheck, setFactCheck] = useState<FactCheckResult | null>(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [showLowMatchModal, setShowLowMatchModal] = useState(false);
  const [resumeHistory, setResumeHistory] = useState<ResumeHistoryItem[]>(() => readResumeHistory());

  const profileText = useMemo(
    () => composeProfileText(contactInfo, experienceForm),
    [contactInfo, experienceForm],
  );
  const hasAnyProfileContent = Boolean(
    contactInfo.name.trim() ||
      experienceForm.education.trim() ||
      experienceForm.skills.trim() ||
      experienceForm.project.trim() ||
      experienceForm.campus.trim(),
  );

  const completedSteps = {
    1: Boolean(jdProfile),
    2: Boolean(contactInfo.name.trim()),
    3: hasAnyProfileContent,
    4: Boolean(diagnosis),
    5: Boolean(resumeResult),
  } satisfies Record<WizardStep, boolean>;

  function updateContact(key: keyof ResumeContactInfo, value: string) {
    setContactInfo((current) => ({ ...current, [key]: value }));
    setSideView("workflow");
    setUserProfile(null);
    setDiagnosis(null);
    setResumeResult(null);
    setError("");
  }

  function updateExperience(key: keyof ExperienceForm, value: string) {
    setExperienceForm((current) => ({ ...current, [key]: value }));
    setSideView("workflow");
    setUserProfile(null);
    setDiagnosis(null);
    setResumeResult(null);
    setError("");
  }

  function fillExampleProfile() {
    setContactInfo(exampleContact);
    setExperienceForm(exampleExperience);
    setSideView("workflow");
    setUserProfile(null);
    setDiagnosis(null);
    setResumeResult(null);
    setError("");
  }

  function appendCompletionSuggestion(suggestion: CompletionSuggestion) {
    setExperienceForm((current) => {
      const currentValue = current[suggestion.target].trim();
      return {
        ...current,
        [suggestion.target]: currentValue
          ? `${currentValue}\n${suggestion.template.trim()}`
          : suggestion.template.trim(),
      };
    });
    setActiveStep(3);
    setSideView("workflow");
    setError("已加入补全模板，请把它改成你真实做过的内容后再重新诊断。");
  }

  function saveResumeToHistory(generated: ResumeGenerateResult) {
    const nextItem: ResumeHistoryItem = {
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}`,
      createdAt: new Date().toISOString(),
      candidateName: generated.resume_json.candidate_name || contactInfo.name || "未命名简历",
      targetTitle: generated.resume_json.target_title || contactInfo.target_title || "目标岗位",
      jdPosition: jdProfile?.position ?? contactInfo.target_title ?? "目标岗位",
      coverageScore: generated.coverage_score,
      contactInfo,
      resumeResult: generated,
    };
    setResumeHistory((current) => {
      const next = [nextItem, ...current].slice(0, 12);
      writeResumeHistory(next);
      return next;
    });
  }

  function openHistoryItem(item: ResumeHistoryItem) {
    setContactInfo(item.contactInfo);
    setResumeResult(item.resumeResult);
    setATSReview(null);
    setFactCheck(null);
    setReviewError("");
    setActiveStep(5);
    setSideView("workflow");
    setError("");
  }

  function deleteHistoryItem(id: string) {
    setResumeHistory((current) => {
      const next = current.filter((item) => item.id !== id);
      writeResumeHistory(next);
      return next;
    });
  }

  async function handleAnalyzeJD() {
    if (!rawJD.trim()) {
      setError("请先粘贴岗位 JD");
      return;
    }

    setLoading("正在分析岗位 JD...");
    setError("");
    setSideView("workflow");
    setJDProfile(null);
    setDiagnosis(null);
    setResumeResult(null);

    try {
      const result = await analyzeJD(rawJD);
      setJDProfile(result.jd_profile);
      setContactInfo((current) => ({
        ...current,
        target_title: current.target_title || result.jd_profile.position || "AI 产品经理",
      }));
      setActiveStep(2);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "岗位 JD 分析失败");
    } finally {
      setLoading("");
    }
  }

  async function runDiagnosis(): Promise<{
    profile: UserProfile;
    result: MatchDiagnoseResult;
  } | null> {
    if (!jdProfile) {
      setError("请先完成岗位 JD 分析");
      setActiveStep(1);
      return null;
    }
    if (!hasAnyProfileContent) {
      setError("请至少填写姓名、教育背景、技能或项目经历中的一项");
      setActiveStep(2);
      return null;
    }

    setLoading("正在诊断匹配度...");
    setError("");

    try {
      const profile = buildUserProfile(contactInfo, experienceForm);
      const result = await diagnoseMatch(jdProfile, profile, profileText, []);
      setUserProfile(profile);
      setDiagnosis(result);
      setActiveStep(4);
      return { profile, result };
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "匹配诊断失败");
      return null;
    } finally {
      setLoading("");
    }
  }

  async function handleGenerateResume(force = false) {
    if (!jdProfile) {
      setError("请先完成岗位 JD 分析");
      setActiveStep(1);
      return;
    }

    let profile = userProfile ?? buildUserProfile(contactInfo, experienceForm);
    let matchResult = diagnosis;

    if (!matchResult) {
      const diagnosed = await runDiagnosis();
      if (!diagnosed) {
        return;
      }
      profile = diagnosed.profile;
      matchResult = diagnosed.result;
    }

    if (!force && isLowMatch(matchResult)) {
      setShowLowMatchModal(true);
      return;
    }

    setShowLowMatchModal(false);
    setLoading("正在生成简历...");
    setError("");
    setReviewError("");
    setATSReview(null);
    setFactCheck(null);

    try {
      const generated = await generateResume(jdProfile, profile);
      setResumeResult(generated);
      saveResumeToHistory(generated);
      setActiveStep(5);
      setLoading("正在检查 ATS 和事实风险...");

      const [atsResult, factResult] = await Promise.allSettled([
        reviewATS(generated.resume_json, jdProfile),
        factCheckResume(generated.resume_json, profile),
      ]);

      if (atsResult.status === "fulfilled") {
        setATSReview(atsResult.value);
      } else {
        setReviewError(atsResult.reason instanceof Error ? atsResult.reason.message : "ATS 检查失败");
      }

      if (factResult.status === "fulfilled") {
        setFactCheck(factResult.value);
      } else {
        setReviewError(factResult.reason instanceof Error ? factResult.reason.message : "事实校验失败");
      }
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "简历生成失败";
      setError(
        message.includes("LLM returned invalid JSON")
          ? "大模型返回格式不稳定，请点击“生成简历”重试；系统会优先使用安全结构化生成，不会编造硬事实。"
          : message,
      );
    } finally {
      setLoading("");
    }
  }

  function renderHistoryView() {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-action">历史简历</p>
            <h2 className="mt-1 text-2xl font-bold text-slate-950">查看之前生成过的简历</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              历史记录保存在当前浏览器里，点击“打开预览”可以继续导出 PDF。
            </p>
          </div>
          <SecondaryButton onClick={() => setSideView("workflow")}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            返回当前流程
          </SecondaryButton>
        </div>

        {resumeHistory.length ? (
          <div className="mt-6 space-y-3">
            {resumeHistory.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-950">
                      {item.candidateName} · {item.targetTitle}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      JD：{item.jdPosition} ｜ 覆盖率 {Math.round(item.coverageScore * 100)}% ｜{" "}
                      {new Date(item.createdAt).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <SecondaryButton onClick={() => openHistoryItem(item)}>打开预览</SecondaryButton>
                    <button
                      type="button"
                      onClick={() => deleteHistoryItem(item.id)}
                      className="inline-flex h-12 items-center justify-center rounded-2xl border border-rose-100 bg-white px-4 text-sm font-bold text-rose-600 transition hover:bg-rose-50"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <History className="mx-auto h-10 w-10 text-slate-400" aria-hidden="true" />
            <h3 className="mt-3 text-lg font-bold text-slate-950">还没有历史简历</h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              生成第一份简历后，这里会自动出现历史记录。
            </p>
          </div>
        )}
      </section>
    );
  }

  function renderCurrentStep() {
    if (sideView === "history") {
      return renderHistoryView();
    }

    if (activeStep === 1) {
      return (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-action">
              <FileText className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-bold text-action">第 1 步</p>
              <h2 className="text-2xl font-bold text-slate-950">粘贴岗位 JD</h2>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            把岗位职责、任职要求、加分项一起粘贴进来。分析完成后，系统会自动进入个人信息填写。
          </p>
          <textarea
            value={rawJD}
            onChange={(event) => {
              setRawJD(event.target.value);
              setError("");
            }}
            rows={16}
            placeholder="在这里粘贴岗位 JD 原文"
            className="mt-5 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-800 outline-none transition focus:border-action focus:bg-white focus:ring-4 focus:ring-teal-50"
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <PrimaryButton onClick={handleAnalyzeJD} disabled={Boolean(loading)}>
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              分析岗位 JD
            </PrimaryButton>
            <SecondaryButton onClick={() => setRawJD(exampleJD)}>填入示例 JD</SecondaryButton>
          </div>
        </section>
      );
    }

    if (activeStep === 2) {
      return (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-action">
              <UserRound className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-bold text-action">第 2 步</p>
              <h2 className="text-2xl font-bold text-slate-950">填写个人信息</h2>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            这些信息只会放在 PDF 顶部。照片第一版使用占位图，后续你可以自己替换。
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <ContactInput label="姓名" value={contactInfo.name} onChange={(value) => updateContact("name", value)} placeholder="请输入姓名" />
            <ContactInput label="求职意向" value={contactInfo.target_title} onChange={(value) => updateContact("target_title", value)} placeholder="AI 产品经理" />
            <ContactInput label="年龄" value={contactInfo.age} onChange={(value) => updateContact("age", value)} placeholder="例如：22岁" />
            <ContactInput label="电话" value={contactInfo.phone} onChange={(value) => updateContact("phone", value)} placeholder="请填写手机号" />
            <ContactInput label="邮箱" value={contactInfo.email} onChange={(value) => updateContact("email", value)} placeholder="name@example.com" />
            <ContactInput label="所在地" value={contactInfo.location} onChange={(value) => updateContact("location", value)} placeholder="城市" />
            <div className="md:col-span-2">
              <ContactInput label="GitHub" value={contactInfo.github} onChange={(value) => updateContact("github", value)} placeholder="https://github.com/username" />
            </div>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => setActiveStep(1)}>
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              上一步
            </SecondaryButton>
            <SecondaryButton onClick={fillExampleProfile}>填入示例信息</SecondaryButton>
            <PrimaryButton onClick={() => setActiveStep(3)}>
              下一步：填写经历
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </PrimaryButton>
          </div>
        </section>
      );
    }

    if (activeStep === 3) {
      return (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-action">
              <ClipboardList className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-bold text-action">第 3 步</p>
              <h2 className="text-2xl font-bold text-slate-950">填写真实经历</h2>
            </div>
          </div>
          <div className="mt-4 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
            写你真实做过的内容即可。不完整也能继续生成，缺的信息不会被编造成事实。
          </div>
          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <TextAreaField
              label="教育背景"
              value={experienceForm.education}
              onChange={(value) => updateExperience("education", value)}
              rows={6}
              placeholder="学校、专业、学历、时间、GPA、课程、奖项"
            />
            <TextAreaField
              label="专业技能"
              value={experienceForm.skills}
              onChange={(value) => updateExperience("skills", value)}
              rows={6}
              placeholder="Python、SQL、Figma、Axure、产品原型、数据分析等"
            />
            <TextAreaField
              label="项目经历"
              value={experienceForm.project}
              onChange={(value) => updateExperience("project", value)}
              rows={8}
              placeholder="项目名、做了什么、用什么工具、产出了什么"
            />
            <TextAreaField
              label="校园 / 竞赛经历"
              value={experienceForm.campus}
              onChange={(value) => updateExperience("campus", value)}
              rows={8}
              placeholder="竞赛、课程设计、学生工作、团队协作等"
            />
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => setActiveStep(2)}>
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              上一步
            </SecondaryButton>
            <SecondaryButton onClick={fillExampleProfile}>填入示例经历</SecondaryButton>
            <PrimaryButton onClick={() => void runDiagnosis()} disabled={Boolean(loading)}>
              诊断匹配度
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </PrimaryButton>
          </div>
        </section>
      );
    }

    if (activeStep === 4) {
      const lowMatch = isLowMatch(diagnosis);
      const completionSuggestions = buildCompletionSuggestions(diagnosis);
      return (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-action">
              <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-bold text-action">第 4 步</p>
              <h2 className="text-2xl font-bold text-slate-950">确认匹配情况</h2>
            </div>
          </div>

          {diagnosis ? (
            <div className={`mt-5 rounded-3xl border p-5 ${lowMatch ? "border-amber-200 bg-amber-50" : "border-teal-100 bg-teal-50"}`}>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-bold text-slate-700">岗位匹配覆盖率</p>
                  <p className="mt-2 text-4xl font-bold text-slate-950">
                    {Math.round(diagnosis.coverage_score * 100)}%
                  </p>
                </div>
                <div className="max-w-lg text-sm leading-6 text-slate-700">
                  {lowMatch
                    ? "当前信息和岗位匹配度偏低。你可以返回补充内容，也可以继续生成，系统只会使用你已经提供的真实信息。"
                    : "当前信息可以继续生成正式简历。系统会优先使用有证据支持的经历。"}
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3 rounded-2xl bg-white/70 p-3">
                <SecondaryButton onClick={() => setActiveStep(3)}>
                  <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                  返回补充信息
                </SecondaryButton>
                <PrimaryButton onClick={() => void handleGenerateResume(false)} disabled={Boolean(loading)}>
                  生成简历
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </PrimaryButton>
              </div>

              {diagnosis.missing_evidence_questions.length > 0 && (
                <div className="mt-5 rounded-2xl bg-white/70 p-4">
                  <p className="text-sm font-bold text-slate-900">如果想提升匹配度，可以补充这些信息</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                    {diagnosis.missing_evidence_questions.slice(0, 5).map((item) => (
                      <li key={`${item.requirement}-${item.question}`}>• {item.question}</li>
                    ))}
                  </ul>
                </div>
              )}

              {completionSuggestions.length > 0 && (
                <div className="mt-5 rounded-2xl border border-blue-100 bg-white p-4">
                  <p className="text-sm font-bold text-slate-900">补全助手</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    这些不是自动编造经历，只是帮你把可以补充的方向放回表单。请改成你真实做过的内容。
                  </p>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {completionSuggestions.map((suggestion) => (
                      <article
                        key={`${suggestion.target}-${suggestion.title}`}
                        className="rounded-2xl border border-slate-200 bg-slate-50 p-3"
                      >
                        <p className="text-sm font-bold text-slate-950">{suggestion.title}</p>
                        <p className="mt-1 text-xs leading-5 text-slate-600">{suggestion.detail}</p>
                        <button
                          type="button"
                          onClick={() => appendCompletionSuggestion(suggestion)}
                          className="mt-3 h-9 rounded-xl bg-slate-950 px-3 text-xs font-bold text-white transition hover:bg-slate-700"
                        >
                          加到{suggestion.target === "skills" ? "专业技能" : suggestion.target === "campus" ? "校园/竞赛" : "项目经历"}
                        </button>
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="text-sm leading-6 text-slate-600">还没有匹配诊断，请先点击下方按钮。</p>
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <SecondaryButton onClick={() => setActiveStep(3)}>
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              返回补充信息
            </SecondaryButton>
            <SecondaryButton onClick={() => void runDiagnosis()} disabled={Boolean(loading)}>
              重新诊断
            </SecondaryButton>
            <PrimaryButton onClick={() => void handleGenerateResume(false)} disabled={Boolean(loading)}>
              生成简历
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </PrimaryButton>
          </div>
        </section>
      );
    }

    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-action">第 5 步</p>
            <h2 className="mt-1 text-2xl font-bold text-slate-950">预览并导出 PDF</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              这里展示的是正式简历预览，不显示系统内部分析标签。
            </p>
          </div>
          {resumeResult && (
            <ExportButton resume={resumeResult.resume_json} contactInfo={contactInfo} className="w-36" />
          )}
        </div>

        {resumeResult ? (
          <div className="mt-5">
            <ResumePreview resume={resumeResult.resume_json} contactInfo={contactInfo} />
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
              {atsReview && <p>ATS 分数：{atsReview.score}，关键词覆盖率：{Math.round(atsReview.keyword_coverage * 100)}%。</p>}
              {factCheck && <p>事实校验风险：{factCheck.risk_level}。{factCheck.summary}</p>}
              {reviewError && <p className="text-amber-700">校验暂时失败：{reviewError}。已生成的简历不会被覆盖。</p>}
            </div>
          </div>
        ) : (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <p className="text-sm leading-6 text-slate-600">还没有生成简历，请返回第 4 步点击“生成简历”。</p>
            <div className="mt-4">
              <PrimaryButton onClick={() => void handleGenerateResume(false)} disabled={Boolean(loading)}>
                生成简历
              </PrimaryButton>
            </div>
          </div>
        )}

        <div className="mt-5">
          <SecondaryButton onClick={() => setActiveStep(4)}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            返回匹配确认
          </SecondaryButton>
        </div>
      </section>
    );
  }

  return (
    <main className="mx-auto max-w-[1280px] px-5 py-6">
      {showLowMatchModal && (
        <LowMatchModal
          onClose={() => setShowLowMatchModal(false)}
          onContinue={() => void handleGenerateResume(true)}
        />
      )}

      <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-teal-50 px-3 py-1 text-sm font-bold text-action">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              JobFit Resume Agent
            </div>
            <h1 className="mt-4 text-3xl font-bold tracking-normal text-slate-950">
              5 步生成正式 PDF 简历
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              跟着步骤填写即可。信息不完整也能生成，系统不会编造你没有提供的硬事实。
            </p>
          </div>
          {loading && (
            <div className="inline-flex items-center gap-2 rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm font-bold text-blue-800">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              {loading}
            </div>
          )}
        </div>
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-3">
          {steps.map((step) => (
            <StepButton
              key={step.step}
              step={step}
              activeStep={activeStep}
              completed={completedSteps[step.step]}
              onClick={() => setActiveStep(step.step)}
            />
          ))}

          <button
            type="button"
            onClick={() => setSideView("history")}
            className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left transition ${
              sideView === "history"
                ? "border-action bg-teal-50 text-slate-950"
                : "border-slate-200 bg-white text-slate-700 hover:border-action hover:text-action"
            }`}
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-700">
              <History className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-bold">历史简历</span>
              <span className="mt-0.5 block truncate text-xs opacity-70">
                {resumeHistory.length ? `${resumeHistory.length} 份已保存` : "查看以前生成的简历"}
              </span>
            </span>
          </button>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-600 shadow-sm">
            <p className="font-bold text-slate-950">当前状态</p>
            <ul className="mt-3 space-y-2">
              <li>• JD：{jdProfile ? "已分析" : "未分析"}</li>
              <li>• 匹配：{diagnosis ? `${Math.round(diagnosis.coverage_score * 100)}%` : "待诊断"}</li>
              <li>• 简历：{resumeResult ? "已生成" : "未生成"}</li>
            </ul>
            {jdProfile && (
              <div className="mt-4 rounded-2xl bg-slate-50 p-3">
                <p className="text-xs font-bold text-slate-500">岗位</p>
                <p className="mt-1 font-bold text-slate-900">{jdProfile.position}</p>
                <p className="mt-1 text-xs text-slate-500">{jdProfile.job_level} · {jdProfile.job_type}</p>
              </div>
            )}
          </div>
        </aside>

        <div>
          {error && (
            <div className="mb-4 rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
              {error}
            </div>
          )}
          {renderCurrentStep()}
        </div>
      </section>
    </main>
  );
}
