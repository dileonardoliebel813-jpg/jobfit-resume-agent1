import type {
  ATSReviewResult,
  FactCheckResult,
  JDProfile,
  MatchAnalysis,
  ResumeJSON,
  UserProfile,
} from "./types";

export const jdProfile: JDProfile = {
  position: "高级产品数据分析师",
  job_level: "中高级",
  job_type: "全职",
  hard_requirements: [
    "熟练使用 SQL 进行数据分析",
    "具备 Python 数据处理经验",
    "能够独立完成产品指标分析",
  ],
  core_tasks: [
    "分析产品漏斗并识别增长机会",
    "支持实验设计和结果解读",
    "向业务团队输出清晰的数据洞察",
  ],
  required_skills: ["SQL", "Python", "产品分析", "实验分析", "沟通表达"],
  preferred_experience: ["有 A/B 测试或增长分析经验", "有跨职能团队协作经验"],
  hidden_preferences: ["偏好能把分析结论转化为产品动作的候选人", "偏好有指标体系建设经验的候选人"],
  resume_strategy: {
    must_highlight: ["量化产品分析成果", "突出 SQL、Python 和实验分析能力"],
    should_weaken: ["弱化与岗位无关的泛运营描述"],
    tone: "结果导向、数据驱动、表达清晰",
  },
};

export const userProfile: UserProfile = {
  name: "Alex Chen",
  headline: "Product analyst with analytics delivery and experiment readout experience.",
  skills: ["SQL", "Python", "Tableau", "Experiment Design", "Product Analytics"],
  experiences: [
    {
      company: "Northstar Labs",
      role: "Product Analyst",
      duration: "2022 - Present",
      highlights: [
        "Built funnel dashboards that helped teams prioritize onboarding fixes.",
        "Designed A/B test readouts and translated results into roadmap decisions.",
      ],
      skills: ["SQL", "Python", "A/B Testing"],
    },
    {
      company: "BrightApps",
      role: "Business Analyst",
      duration: "2020 - 2022",
      highlights: ["Automated weekly reporting and reduced manual analysis time."],
      skills: ["SQL", "Tableau"],
    },
  ],
  education: ["B.S. Information Systems, Mock University"],
};

export const matchAnalysis: MatchAnalysis = {
  overall_score: 0.84,
  matched_skills: [
    { skill: "SQL", score: 0.92, evidence: "Dashboard and reporting work." },
    { skill: "Python", score: 0.88, evidence: "Analysis automation and funnel work." },
    { skill: "Product Analytics", score: 0.86, evidence: "Product analyst experience." },
    { skill: "Stakeholder Communication", score: 0.7, evidence: "Readouts and presentations." },
  ],
  gaps: ["Causal analysis"],
  recommendations: [
    "Lead with product analytics impact.",
    "Use ATS keywords in summary and experience bullets.",
    "Confirm any quantified claims before export.",
  ],
};

export const resumeJson: ResumeJSON = {
  candidate_name: "Alex Chen",
  target_title: "Senior Product Data Analyst",
  headline: "Data-driven product analyst focused on metrics, experiments, and product decisions.",
  summary: [
    {
      text: "具备 SQL、Python 与产品指标分析基础，能够围绕漏斗、实验和业务问题整理分析路径。",
      evidence_status: "supported",
      risk_level: "low",
    },
    {
      text: "有产品分析和跨团队沟通经验，能够将数据结论转化为可讨论的产品优化建议。",
      evidence_status: "supported",
      risk_level: "low",
    },
    {
      text: "熟悉 dashboard、A/B testing 与产品指标表达，能够支持团队做实验结果解读。",
      evidence_status: "transferable",
      risk_level: "low",
    },
  ],
  skills: [
    "SQL",
    "Python",
    "A/B testing",
    "dashboard",
    "product metrics",
    "Tableau",
    "Product Analytics",
    "Experiment Design",
    "Stakeholder Communication",
    "Data Storytelling",
  ],
  projects: [
    {
      title: "Product Funnel Analytics Project",
      subtitle: "2022 - Present | Product Analyst",
      bullets: [
        {
          text: "Built funnel dashboards to help product teams identify onboarding friction and prioritize follow-up analysis.",
          evidence_status: "supported",
          risk_level: "low",
        },
        {
          text: "Designed A/B test readouts and translated experiment results into roadmap discussion inputs.",
          evidence_status: "supported",
          risk_level: "low",
        },
        {
          text: "Organized product metrics, cohort views, and stakeholder questions into reusable dashboard analysis notes.",
          evidence_status: "transferable",
          risk_level: "low",
        },
        {
          text: "Used SQL and Python to support recurring analysis workflows and reduce repetitive reporting effort.",
          evidence_status: "supported",
          risk_level: "low",
        },
      ],
    },
  ],
  practice_experiences: [
    {
      title: "Analytics Delivery Practice",
      subtitle: "Product analysis collaboration",
      bullets: [
        {
          text: "Assisted weekly reporting automation and kept analysis outputs aligned with business review needs.",
          evidence_status: "supported",
          risk_level: "low",
        },
        {
          text: "Coordinated metric definitions with stakeholders before presenting dashboard conclusions.",
          evidence_status: "transferable",
          risk_level: "low",
        },
        {
          text: "Documented analysis assumptions and follow-up questions to keep product decisions traceable.",
          evidence_status: "inferred",
          risk_level: "medium",
        },
      ],
    },
  ],
  campus_or_competition: [
    {
      title: "Business Analysis Training",
      subtitle: "Information Systems background",
      bullets: [
        {
          text: "Developed structured problem-solving habits through information systems coursework and analytics projects.",
          evidence_status: "transferable",
          risk_level: "low",
        },
        {
          text: "Practiced clear written communication through recurring reports, dashboards, and analysis summaries.",
          evidence_status: "transferable",
          risk_level: "low",
        },
      ],
    },
  ],
  education: ["B.S. Information Systems, Mock University"],
  self_evaluation: [
    {
      text: "关注数据结论能否被产品和业务团队理解，并习惯保留分析依据。",
      evidence_status: "transferable",
      risk_level: "low",
    },
    {
      text: "能够在指标、实验和用户路径之间建立联系，支持产品判断。",
      evidence_status: "transferable",
      risk_level: "low",
    },
    {
      text: "表达风格偏结构化，适合需要持续沟通和复盘的产品分析岗位。",
      evidence_status: "inferred",
      risk_level: "medium",
    },
  ],
  side_report: {
    missing_info: ["可继续补充更具体的实验样本、指标口径和业务背景。"],
    weak_match_points: ["部分产品决策影响需要用户进一步确认。"],
    suggested_user_inputs: ["补充最有代表性的 dashboard 或实验案例。"],
    assumptions_need_confirmation: ["部分能力迁移表达需要候选人确认符合真实经历。"],
    match_gap_summary: "当前示例基于 mock 经历生成，正式使用前需要替换为真实经历。",
  },
};

export const atsReview: ATSReviewResult = {
  score: 86,
  keyword_coverage: 0.82,
  summary: "Mock ATS review passed with minor keyword and formatting suggestions.",
  issues: [
    {
      category: "keywords",
      severity: "low",
      message: "Keyword coverage is acceptable for the mock JD profile.",
      suggestion: "Keep role-critical keywords in both skills and experience bullets.",
    },
  ],
};

export const factCheck: FactCheckResult = {
  risk_level: "medium",
  summary: "Generated claims are mapped to profile evidence, with summary wording pending review.",
  items: [
    {
      claim: resumeJson.summary[0].text,
      status: "inferred",
      source_hint: "candidate profile summary",
      note: "Confirm positioning language before export.",
    },
  ],
};
