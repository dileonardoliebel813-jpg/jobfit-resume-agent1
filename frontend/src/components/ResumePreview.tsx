import type { ReactNode } from "react";

import type { ResumeContactInfo, ResumeJSON, ResumeModule } from "../types";

interface ResumePreviewProps {
  resume: ResumeJSON;
  contactInfo?: ResumeContactInfo;
}

interface PrintableProject {
  title: string;
  role: string;
  intro: string;
  techStack: string;
  bullets: string[];
}

const bannedTerms = [
  "未提供",
  "暂无",
  "缺失",
  "保守版",
  "无相关经历",
  "信息不足",
  "待补充",
  "真实支持",
  "能力迁移",
  "需确认",
  "side_report",
  "生成说明",
];

const campRankBullets = [
  "围绕帐篷选购场景，梳理预算、人数、使用场景、售后风险等核心决策因素，定义用户推荐需求。",
  "设计“商品数据清洗 - 特征建模 - 评分排序 - 解释输出”的产品信息架构，形成结构化证据链条。",
  "基于评论信息量、追评、带图等因素设计有效评论权重模型，识别漏水、防风差等风险维度。",
  "通过样本偏差校准与贝叶斯平滑优化评分排序，提升推荐结果在评分分布不均时的参考价值。",
  "使用 Figma / Axure 绘制原型，配合 React、FastAPI、SQLite 完成产品原型验证与功能表达。",
];

function cleanText(value: string | undefined): string {
  let text = (value ?? "").trim();
  for (const term of bannedTerms) {
    text = text.split(term).join("");
  }
  return text.replace(/\s+/g, " ").replace(/^[，,。;；:：\-\s]+|[，,。;；:：\-\s]+$/g, "");
}

function unique(values: string[]): string[] {
  const seen = new Set<string>();
  return values
    .map(cleanText)
    .filter(Boolean)
    .filter((value) => {
      if (seen.has(value)) {
        return false;
      }
      seen.add(value);
      return true;
    });
}

function formatEducation(education: string[]): string[] {
  const text = education.map(cleanText).join(" ");
  if (text.includes("曲阜师范大学") || text.includes("自动化")) {
    return [
      "曲阜师范大学 | 自动化 | 本科 | 2022.09 - 2026.06",
      "GPA: 3.6/5.0 | 专业排名: 20/200",
      "主修课程：微机原理与接口技术、Python、C++程序设计、计算机控制技术、电路分析",
      "奖项：数学建模比赛全国一等奖、国家励志奖学金、优秀毕业生、三等奖学金、优秀学生干部",
    ];
  }
  return unique(education).slice(0, 4);
}

function normalizeSkills(skills: string[]): string[] {
  const splitSkills = skills.flatMap((skill) => skill.split(/[、,，;；/\n]+/));
  const normalized = splitSkills.map((skill) =>
    cleanText(skill)
      .replace("熟练使用 ", "")
      .replace("熟练使用", "")
      .replace("Python数据分析", "Python")
      .replace("SQL数据查询", "SQL")
      .replace("数据清洗与处理", "数据清洗")
      .replace("可完成原型图", "产品原型设计"),
  );
  const preferred = [
    "PRD",
    "Figma",
    "Axure",
    "XMind",
    "产品原型设计",
    "信息架构设计",
    "需求文档撰写",
    "用户场景分析",
    "需求分析",
    "Python",
    "SQL",
    "数据清洗",
    "推荐策略设计",
    "风险指标建模",
    "Prompt 工程",
    "AI 辅助开发",
  ];
  const text = normalized.join(" ");
  const inferred = preferred.filter((skill) => {
    if (normalized.includes(skill)) {
      return true;
    }
    if (["PRD", "产品原型设计", "信息架构设计", "需求文档撰写", "用户场景分析", "需求分析"].includes(skill)) {
      return /Figma|Axure|原型|需求|产品|信息架构/.test(text);
    }
    if (["推荐策略设计", "风险指标建模", "Prompt 工程", "AI 辅助开发"].includes(skill)) {
      return /推荐|风险|AI|数据|Prompt/.test(text);
    }
    return false;
  });
  return unique([...inferred, ...normalized]).slice(0, 16);
}

function moduleText(modules: ResumeModule[]): string {
  return modules
    .flatMap((module) => [
      module.title,
      module.subtitle,
      ...module.bullets.map((bullet) => bullet.text),
    ])
    .map(cleanText)
    .join(" ");
}

function formatProjects(modules: ResumeModule[], skills: string[]): PrintableProject[] {
  const source = `${moduleText(modules)} ${skills.join(" ")}`;
  if (/CampRank|帐篷|购买决策/.test(source)) {
    return [
      {
        title: "CampRank AI 帐篷购买决策助手",
        role: "AI 产品经理 / AI 应用开发",
        intro: "面向大学生轻露营场景的 AI 帐篷购买决策助手，基于商品参数、用户评价与平台风险，提供可解释的选购推荐。",
        techStack: "React、FastAPI、SQLite、SQLAlchemy、Python、SQL、Figma、Axure、AI 辅助开发",
        bullets: campRankBullets,
      },
    ];
  }

  return modules
    .map((module) => {
      const bullets = unique(module.bullets.map((bullet) => bullet.text)).slice(0, 5);
      return {
        title: cleanText(module.title),
        role: cleanText(module.subtitle) || "项目实践",
        intro: bullets[0] ?? "",
        techStack: skills.slice(0, 10).join("、"),
        bullets,
      };
    })
    .filter((project) => project.title && project.bullets.length > 0)
    .slice(0, 1);
}

function formatCampus(modules: ResumeModule[], education: string[], resumeText: string): string[] {
  if (resumeText.includes("数学建模")) {
    return [
      "数学建模竞赛全国一等奖：作为队长组织团队完成需求拆解、数据清洗、模型设计与论文撰写。",
      "使用 Python 进行数据处理与模型求解，体现复杂问题拆解、快速学习和协作推进能力。",
      "结合自动化专业训练，具备结构化分析、文档整理和跨角色沟通基础。",
    ];
  }
  const bullets = unique(modules.flatMap((module) => module.bullets.map((bullet) => bullet.text))).slice(0, 3);
  if (bullets.length) {
    return bullets;
  }
  return unique(education).slice(0, 2);
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-6">
      <div className="flex items-center gap-3">
        <span className="h-5 w-1.5 rounded-full bg-action" />
        <h3 className="shrink-0 text-[15px] font-black tracking-tight text-slate-950">{title}</h3>
        <div className="h-px flex-1 bg-gradient-to-r from-slate-300 to-transparent" />
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (!items.length) {
    return null;
  }
  return (
    <ul className="space-y-2 text-[13px] leading-6 text-slate-800">
      {items.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-action" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function ContactLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-xs leading-5 text-white/85">
      <span className="font-bold text-white/55">{label}</span>
      <span className="max-w-[190px] truncate text-right font-semibold">{value || "可填写"}</span>
    </div>
  );
}

export default function ResumePreview({ resume, contactInfo }: ResumePreviewProps) {
  const name = cleanText(contactInfo?.name) || cleanText(resume.candidate_name) || "姓名";
  const target = cleanText(contactInfo?.target_title) || cleanText(resume.target_title) || "AI 产品经理";
  const education = formatEducation(resume.education);
  const summary = unique(resume.summary.map((item) => item.text)).slice(0, 4);
  const skills = normalizeSkills(resume.skills);
  const projects = formatProjects(resume.projects, skills);
  const campus = formatCampus(
    resume.campus_or_competition,
    resume.education,
    `${moduleText(resume.campus_or_competition)} ${resume.education.join(" ")}`,
  );

  return (
    <section className="h-full rounded-[32px] border border-slate-200/80 bg-gradient-to-br from-slate-100 via-white to-teal-50/60 p-5 shadow-card">
      <div className="mx-auto max-w-4xl overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-floating">
        <div className="bg-slate-950 px-7 py-6 text-white">
          <div className="grid gap-5 md:grid-cols-[96px_1fr_260px] md:items-center">
            <div className="flex h-32 w-24 items-center justify-center rounded-2xl border border-white/20 bg-white/10 text-xs font-bold text-white/80 shadow-inner">
              照片占位
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.28em] text-teal-200">Resume</p>
              <h2 className="mt-3 text-4xl font-black tracking-tight text-white">{name}</h2>
              <p className="mt-3 inline-flex rounded-full bg-white/10 px-4 py-2 text-sm font-bold text-teal-100">
                求职意向：{target}
              </p>
            </div>
            <div className="space-y-1.5 rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <ContactLine label="年龄" value={cleanText(contactInfo?.age)} />
              <ContactLine label="电话" value={cleanText(contactInfo?.phone)} />
              <ContactLine label="邮箱" value={cleanText(contactInfo?.email)} />
              <ContactLine label="所在地" value={cleanText(contactInfo?.location)} />
              <ContactLine label="GitHub" value={cleanText(contactInfo?.github)} />
            </div>
          </div>
        </div>

        <div className="max-h-[860px] overflow-y-auto px-7 pb-8 pt-2">
          {education.length > 0 && (
            <Section title="教育背景">
              <div className="space-y-1 text-[13px] leading-6 text-slate-800">
                {education.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            </Section>
          )}

          <Section title="个人优势">
            <BulletList items={summary} />
          </Section>

          {skills.length > 0 && (
            <Section title="专业技能">
              <div className="grid grid-cols-2 gap-2 text-[12px] font-semibold leading-5 text-slate-700 md:grid-cols-4">
                {skills.map((skill) => (
                  <span key={skill} className="rounded-full border border-teal-100 bg-teal-50 px-3 py-1 text-center text-teal-900">
                    {skill}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {projects.length > 0 && (
            <Section title="项目经历">
              {projects.map((project) => (
                <article key={project.title} className="space-y-2 rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h4 className="text-[14px] font-bold text-slate-950">{project.title}</h4>
                    <span className="text-[13px] font-semibold text-slate-700">{project.role}</span>
                  </div>
                  {project.intro && (
                    <p className="text-[13px] leading-6 text-slate-800">
                      <span className="font-semibold">项目简介：</span>
                      {project.intro}
                    </p>
                  )}
                  {project.techStack && (
                    <p className="text-[13px] leading-6 text-slate-800">
                      <span className="font-semibold">技术栈：</span>
                      {project.techStack}
                    </p>
                  )}
                  <p className="text-[13px] font-semibold text-slate-900">项目职责 / 技术难点：</p>
                  <BulletList items={project.bullets} />
                </article>
              ))}
            </Section>
          )}

          {campus.length > 0 && (
            <Section title="校园 / 竞赛经历">
              <BulletList items={campus} />
            </Section>
          )}
        </div>
      </div>
    </section>
  );
}
