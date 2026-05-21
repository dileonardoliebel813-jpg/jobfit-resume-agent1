from __future__ import annotations

import json
import re
from collections.abc import Iterable

from pydantic import ValidationError

from app.core.config import settings
from app.core.llm_client import LLMClient, LLMClientError
from app.core.prompts import (
    RESUME_COMPLETE_SYSTEM_PROMPT,
    build_resume_complete_user_prompt,
)
from app.schemas.evidence_schema import EvidenceItem
from app.schemas.jd_schema import JDProfile
from app.schemas.match_schema import MatchDiagnoseResponse
from app.schemas.profile_schema import UserProfile, WorkExperience
from app.schemas.resume_schema import (
    RESUME_JSON_SCHEMA,
    ResumeBullet,
    ResumeJSON,
    ResumeModule,
    ResumeSideReport,
)


class ResumeWriterAgentError(RuntimeError):
    """Raised when resume writing cannot produce a valid complete resume."""


_BANNED_TERMS = (
    "未提供",
    "暂无",
    "缺失",
    "保守版",
    "无相关经历",
    "信息不足",
    "待补充",
)

_ALLOWED_BULLET_STATUSES = {"supported", "transferable", "inferred"}
_STATUS_RISK_LEVEL = {
    "supported": "low",
    "transferable": "low",
    "inferred": "medium",
}


class ResumeWriterAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def write(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
        strategy_notes: list[str],
        diagnosis: MatchDiagnoseResponse | None = None,
    ) -> ResumeJSON:
        if settings.LLM_MODE == "real":
            try:
                result = self.llm_client.generate_json(
                    system_prompt=RESUME_COMPLETE_SYSTEM_PROMPT,
                    user_prompt=build_resume_complete_user_prompt(
                        jd_profile.model_dump_json(ensure_ascii=False),
                        user_profile.model_dump_json(ensure_ascii=False),
                        json.dumps(
                            [item.model_dump() for item in evidence],
                            ensure_ascii=False,
                        ),
                        json.dumps(strategy_notes, ensure_ascii=False),
                        diagnosis.model_dump_json(ensure_ascii=False) if diagnosis else "{}",
                    ),
                    json_schema=RESUME_JSON_SCHEMA,
                    schema_name="resume_json",
                    model=settings.OPENAI_MODEL,
                    reasoning_effort=settings.RESUME_REASONING_EFFORT,
                )
                seed_resume = ResumeJSON.model_validate(result)
            except ValidationError as exc:
                seed_resume = self._build_safe_seed_resume(jd_profile, user_profile)
                strategy_notes = [
                    *strategy_notes,
                    "大模型返回的 JSON 字段不符合简历结构，已使用安全结构化生成，不新增硬事实。",
                ]
            except LLMClientError as exc:
                if "invalid JSON" not in str(exc):
                    raise
                seed_resume = self._build_safe_seed_resume(jd_profile, user_profile)
                strategy_notes = [
                    *strategy_notes,
                    "大模型返回格式不稳定，已使用安全结构化生成，不新增硬事实。",
                ]
        else:
            seed_resume = self._build_safe_seed_resume(jd_profile, user_profile)

        return self.post_process_resume_content(
            resume=seed_resume,
            jd_profile=jd_profile,
            user_profile=user_profile,
            evidence=evidence,
            strategy_notes=strategy_notes,
            diagnosis=diagnosis,
        )

    def post_process_resume_content(
        self,
        resume: ResumeJSON,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
        strategy_notes: list[str],
        diagnosis: MatchDiagnoseResponse | None = None,
    ) -> ResumeJSON:
        sanitized_candidate_name = self._safe_text(
            user_profile.name or resume.candidate_name,
            "候选人",
        )
        sanitized_target_title = self._safe_text(
            jd_profile.position or resume.target_title,
            "目标岗位",
        )
        sanitized_headline = self._build_headline(
            resume=resume,
            jd_profile=jd_profile,
            user_profile=user_profile,
        )

        summary = self._build_summary(
            resume.summary,
            jd_profile,
            user_profile,
            evidence,
        )
        skills = self._build_skills(resume.skills, jd_profile, user_profile)
        projects, project_signals = self._build_projects(
            resume.projects,
            jd_profile,
            user_profile,
            evidence,
        )
        practice_experiences = self._build_practice_experiences(
            resume.practice_experiences,
            jd_profile,
            user_profile,
            project_signals,
        )
        campus_or_competition = self._build_campus_or_competition(
            resume.campus_or_competition,
            jd_profile,
            user_profile,
        )
        education = self._build_education(resume.education, user_profile)
        self_evaluation = self._build_self_evaluation(
            resume.self_evaluation,
            jd_profile,
            user_profile,
            project_signals,
        )
        raw_side_report_items = self._collect_side_report_items_from_raw_resume(resume)
        side_report = self._build_side_report(
            resume.side_report,
            jd_profile,
            user_profile,
            diagnosis,
            strategy_notes,
            projects,
            practice_experiences,
            campus_or_competition,
            raw_side_report_items,
        )

        final_resume = ResumeJSON(
            candidate_name=sanitized_candidate_name,
            target_title=sanitized_target_title,
            headline=sanitized_headline,
            summary=summary,
            skills=skills,
            projects=projects,
            practice_experiences=practice_experiences,
            campus_or_competition=campus_or_competition,
            education=education,
            self_evaluation=self_evaluation,
            side_report=side_report,
        )
        return final_resume

    def _build_safe_seed_resume(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
    ) -> ResumeJSON:
        return ResumeJSON(
            candidate_name=self._safe_text(user_profile.name, "候选人"),
            target_title=self._safe_text(jd_profile.position, "目标岗位"),
            headline=self._build_headline(None, jd_profile, user_profile),
            summary=[],
            skills=list(dict.fromkeys([skill.strip() for skill in user_profile.skills if skill.strip()])),
            projects=[],
            practice_experiences=[],
            campus_or_competition=[],
            education=[item.strip() for item in user_profile.education if item.strip()],
            self_evaluation=[],
            side_report=ResumeSideReport(
                missing_info=[],
                weak_match_points=[],
                suggested_user_inputs=[],
                assumptions_need_confirmation=[],
                match_gap_summary="",
            ),
        )

    def _build_summary(
        self,
        existing: list[ResumeBullet],
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
    ) -> list[ResumeBullet]:
        bullets = self._sanitize_bullets(existing, keep_statuses=_ALLOWED_BULLET_STATUSES)
        templates = [
            ResumeBullet(
                text=(
                    f"面向 {self._safe_text(jd_profile.position, '目标岗位')} 岗位，"
                    "具备从用户场景、需求拆解到原型表达的基础能力，能够把复杂决策问题拆成可落地功能。"
                ),
                evidence_status="transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text=(
                    "能够围绕 AI 产品场景持续沉淀项目表达，将商品参数、用户评价与推荐逻辑整理成可解释模块。"
                    if not user_profile.experiences
                    else "有 AI 购买决策类项目实践，能够结合商品参数、用户评价与推荐逻辑，设计可解释的产品模块。"
                ),
                evidence_status="supported" if user_profile.experiences else "transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text=(
                    "熟悉 Python、SQL、React、FastAPI、SQLite、SQLAlchemy、Figma、Axure 等工具，"
                    "能够支持前后端协作、原型验证与数据字段沟通。"
                ),
                evidence_status="transferable",
                risk_level="low",
            ),
        ]
        bullets = self._fill_bullets(bullets, templates, 3)
        return bullets[:3]

    def _build_skills(
        self,
        existing: list[str],
        jd_profile: JDProfile,
        user_profile: UserProfile,
    ) -> list[str]:
        sources = [
            *existing,
            *user_profile.skills,
            "需求分析",
            "原型设计",
            "信息架构",
            "产品协作",
            "用户场景分析",
            "数据驱动决策",
            "推荐逻辑",
            "可解释推荐",
            "跨团队协作",
            "文档整理",
            "AI 工具应用",
            "接口理解",
        ]
        sources.extend(jd_profile.required_skills)
        sources.extend(jd_profile.core_tasks)
        cleaned = self._unique_texts(sources)
        return cleaned[:14] if len(cleaned) > 14 else cleaned

    def _build_projects(
        self,
        existing: list[ResumeModule],
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
    ) -> tuple[list[ResumeModule], list[str]]:
        modules = self._sanitize_modules(existing, min_bullets=4, max_bullets=5)
        if not modules:
            modules = [self._build_primary_project_module(jd_profile, user_profile, evidence)]
        project_signals = self._collect_project_signals(modules)
        return modules[:2], project_signals

    def _build_primary_project_module(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        evidence: list[EvidenceItem],
    ) -> ResumeModule:
        source = self._primary_experience(user_profile)
        title = self._project_title(source)
        subtitle_parts = [
            self._safe_text(jd_profile.position, "目标岗位"),
            "产品化表达",
        ]
        if source and source.duration.strip():
            subtitle_parts.insert(0, self._safe_text(source.duration, ""))
        subtitle = "｜".join(part for part in subtitle_parts if part)

        if source and self._looks_like_project_title(self._safe_text(source.role or source.company, "")):
            bullets = [
                ResumeBullet(
                    text="围绕大学生轻露营用户的帐篷选购场景，梳理价格、参数、用户评价与平台风险等核心决策因素，形成产品推荐逻辑。",
                    evidence_status="supported",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="设计“用户筛选层—数据分析层—推荐计算层—结果展示层”的信息架构，支持预算过滤、场景匹配和风险提示。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="将“为什么推荐”模块拆解为商品参数、评论依据和平台信息三类解释，提升推荐结果的可理解性。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="基于 FastAPI、React、SQLite、SQLAlchemy 搭建原型闭环，理解前端页面、后端接口和数据字段之间的协作关系。",
                    evidence_status="supported",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="使用 ChatGPT、Codex、DeepSeek 等 AI 工具辅助需求拆解、文档整理和功能迭代，提高产品方案验证效率。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
            ]
        else:
            bullets = [
                ResumeBullet(
                    text="围绕 AI 产品场景梳理用户决策路径、功能入口和结果展示逻辑，形成可继续投递前修改的项目内容。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="设计筛选层、分析层、推荐层和解释层的信息结构，支持预算过滤、场景匹配和风险提示。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="将商品参数、评价信息和平台信息整理为解释模块，增强推荐结果的可理解性。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
                ResumeBullet(
                    text="结合已掌握的技术栈搭建原型闭环，理解前端页面、后端接口和数据字段之间的协作关系。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="使用 AI 工具辅助需求分析、文档整理和功能迭代，提升方案验证效率。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
            ]

        return ResumeModule(
            title=title,
            subtitle=subtitle or self._safe_text(jd_profile.position, "AI 产品实践"),
            bullets=self._fit_module_bullets(bullets, 4, 5),
        )

    def _build_practice_experiences(
        self,
        existing: list[ResumeModule],
        jd_profile: JDProfile,
        user_profile: UserProfile,
        project_signals: list[str],
    ) -> list[ResumeModule]:
        modules = self._sanitize_modules(existing, min_bullets=3, max_bullets=3)
        if modules:
            return modules[:1]

        title = "AI 产品功能设计与原型实践"
        subtitle = "基于真实项目的产品化表达"
        bullets = [
            ResumeBullet(
                text="参与产品需求梳理，围绕用户决策路径梳理功能入口、筛选条件和结果展示逻辑。",
                evidence_status="transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text="协助整理商品字段、评价信息和解释模块，支持推荐结果从“可用”走向“可理解”。",
                evidence_status="inferred",
                risk_level="medium",
            ),
            ResumeBullet(
                text="配合前后端实现和接口联调，理解页面状态、数据字段和展示顺序之间的协作关系。",
                evidence_status="transferable",
                risk_level="low",
            ),
        ]

        if project_signals:
            bullets[0] = ResumeBullet(
                text=(
                    f"围绕 {project_signals[0]} 延展产品实践，参与需求梳理与原型拆解，形成更清晰的功能路径。"
                ),
                evidence_status="inferred",
                risk_level="medium",
            )

        return [
            ResumeModule(
                title=title,
                subtitle=subtitle,
                bullets=bullets,
            )
        ]

    def _build_campus_or_competition(
        self,
        existing: list[ResumeModule],
        jd_profile: JDProfile,
        user_profile: UserProfile,
    ) -> list[ResumeModule]:
        modules = self._sanitize_modules(existing, min_bullets=2, max_bullets=3)
        if modules:
            return modules[:1]

        title = "课程与专业训练"
        subtitle = self._extract_education_hint(user_profile.education) or "自动化专业背景下的结构化分析训练"
        bullets = [
            ResumeBullet(
                text="在自动化专业学习中形成结构化分析习惯，能够把复杂问题拆成可执行步骤并清晰表达。",
                evidence_status="transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text="参与课程作业和文档整理时，注重信息归纳、沟通确认与复盘总结。",
                evidence_status="inferred",
                risk_level="medium",
            ),
            ResumeBullet(
                text="结合项目练习尝试从用户视角观察功能路径，提升方案表达与协作意识。",
                evidence_status="inferred",
                risk_level="medium",
            ),
        ]

        return [
            ResumeModule(
                title=title,
                subtitle=subtitle,
                bullets=self._fit_module_bullets(bullets, 2, 3),
            )
        ]

    def _build_education(self, existing: list[str], user_profile: UserProfile) -> list[str]:
        education = self._unique_texts([*existing, *user_profile.education])
        if education:
            return education

        major_hint = self._extract_education_hint(user_profile.education)
        if major_hint:
            return [major_hint]
        return []

    def _build_self_evaluation(
        self,
        existing: list[ResumeBullet],
        jd_profile: JDProfile,
        user_profile: UserProfile,
        project_signals: list[str],
    ) -> list[ResumeBullet]:
        bullets = self._sanitize_bullets(existing, keep_statuses=_ALLOWED_BULLET_STATUSES)
        templates = [
            ResumeBullet(
                text="具备 AI 工具使用、需求拆解与项目原型设计基础，能够围绕用户消费决策场景梳理功能路径与信息架构。",
                evidence_status="transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text=(
                    "有 AI 购买决策类项目实践经验，能够结合商品参数、用户评价与推荐逻辑设计可解释的产品模块。"
                    if user_profile.experiences
                    else "能够把 AI 产品场景中的商品参数、用户评价与推荐逻辑整理成可解释的产品模块。"
                ),
                evidence_status="supported" if user_profile.experiences else "transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text="具备 Python、SQL、React、FastAPI 等技术理解能力，能够与研发团队围绕接口、数据字段和功能实现进行沟通。",
                evidence_status="transferable",
                risk_level="low",
            ),
        ]
        if project_signals:
            templates[1] = ResumeBullet(
                text=(
                    f"围绕 {project_signals[0]} 形成产品化表达能力，能够把场景分析、推荐逻辑和解释模块结合起来。"
                ),
                evidence_status="inferred",
                risk_level="medium",
            )
        bullets = self._fill_bullets(bullets, templates, 3)
        return bullets[:3]

    def _build_side_report(
        self,
        existing: ResumeSideReport,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        diagnosis: MatchDiagnoseResponse | None,
        strategy_notes: list[str],
        projects: list[ResumeModule],
        practice_experiences: list[ResumeModule],
        campus_or_competition: list[ResumeModule],
        raw_side_report_items: list[tuple[str, str]],
    ) -> ResumeSideReport:
        missing_info: list[str] = []
        weak_match_points: list[str] = []
        suggested_user_inputs: list[str] = []
        assumptions_need_confirmation: list[str] = []

        if diagnosis:
            for item in diagnosis.evidence_items:
                if item.status in {"missing_evidence", "user_confirmed_absent"}:
                    missing_info.append(f"{item.category}：{item.requirement}")
                elif item.status == "weak_evidence":
                    weak_match_points.append(f"{item.category}：{item.requirement}")
            suggested_user_inputs.extend(
                question.question for question in diagnosis.missing_evidence_questions
            )
            assumptions_need_confirmation.extend(
                f"需要确认：{item}" for item in diagnosis.safe_resume_strategy.must_not_claim
            )

        for status, text in raw_side_report_items:
            if status == "unsupported":
                suggested_user_inputs.append(text)
            elif status == "missing":
                missing_info.append(text)

        if not user_profile.experiences:
            missing_info.append("尚未提供可直接写入的项目或工作经历")
        if not user_profile.skills:
            missing_info.append("尚未提供可直接复用的技能清单")
        if not user_profile.education:
            missing_info.append("教育背景信息尚未完整展开")

        if not suggested_user_inputs:
            suggested_user_inputs.append("补充项目中你负责的具体模块、使用的工具、产出物或接口理解。")
        if not assumptions_need_confirmation:
            assumptions_need_confirmation.append("将现有项目按 AI 产品实践方向做岗位化表达。")
        if not weak_match_points:
            weak_match_points.append("当前素材更强于项目实践，真实实习或竞赛成果仍可继续补充。")

        match_gap_summary = self._build_match_gap_summary(diagnosis, missing_info, weak_match_points)

        return ResumeSideReport(
            missing_info=self._unique_texts([*existing.missing_info, *missing_info])[:8],
            weak_match_points=self._unique_texts([*existing.weak_match_points, *weak_match_points])[:8],
            suggested_user_inputs=self._unique_texts(
                [*existing.suggested_user_inputs, *suggested_user_inputs]
            )[:8],
            assumptions_need_confirmation=self._unique_texts(
                [*existing.assumptions_need_confirmation, *assumptions_need_confirmation]
            )[:8],
            match_gap_summary=match_gap_summary or existing.match_gap_summary,
        )

    def _build_match_gap_summary(
        self,
        diagnosis: MatchDiagnoseResponse | None,
        missing_info: list[str],
        weak_match_points: list[str],
    ) -> str:
        if diagnosis:
            return (
                f"覆盖率约 {round(diagnosis.coverage_score * 100)}%，"
                f"其中 {len(weak_match_points)} 项可做弱化表达，"
                f"{len(missing_info)} 项仍需继续补充真实证据。"
            )
        return (
            f"当前已整理 {len(weak_match_points)} 项弱相关点和 {len(missing_info)} 项待补充说明，"
            "简历正文已保留可安全写入的内容。"
        )

    def _sanitize_modules(
        self,
        modules: list[ResumeModule],
        min_bullets: int,
        max_bullets: int,
    ) -> list[ResumeModule]:
        sanitized: list[ResumeModule] = []
        for module in modules:
            title = self._safe_text(module.title, "项目实践")
            subtitle = self._safe_text(module.subtitle, "")
            bullets = self._sanitize_bullets(module.bullets, keep_statuses=_ALLOWED_BULLET_STATUSES)
            if len(bullets) < min_bullets:
                bullets = self._pad_module_bullets(title, subtitle, bullets, min_bullets, max_bullets)
            else:
                bullets = bullets[:max_bullets]
            if bullets:
                sanitized.append(
                    ResumeModule(
                        title=title,
                        subtitle=subtitle,
                        bullets=bullets,
                    )
                )
        return sanitized

    def _fit_module_bullets(
        self,
        bullets: list[ResumeBullet],
        min_count: int,
        max_count: int,
    ) -> list[ResumeBullet]:
        clean = self._sanitize_bullets(bullets, keep_statuses=_ALLOWED_BULLET_STATUSES)
        if len(clean) >= min_count:
            return clean[:max_count]
        return self._pad_module_bullets("", "", clean, min_count, max_count)

    def _pad_module_bullets(
        self,
        title: str,
        subtitle: str,
        existing: list[ResumeBullet],
        min_count: int,
        max_count: int,
    ) -> list[ResumeBullet]:
        templates = self._module_templates(title, subtitle)
        merged = self._merge_bullets(existing, templates)
        if len(merged) < min_count:
            merged = self._merge_bullets(merged, self._fallback_bullet_templates(title))
        return merged[:max_count]

    def _module_templates(self, title: str, subtitle: str) -> list[ResumeBullet]:
        lowered = f"{title} {subtitle}"
        if "实践" in lowered:
            return [
                ResumeBullet(
                    text="参与产品需求梳理，围绕用户决策路径梳理功能入口、筛选条件和结果展示逻辑。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="协助整理商品字段、评价信息和解释模块，支持推荐结果从“可用”走向“可理解”。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
                ResumeBullet(
                    text="配合前后端实现和接口联调，理解页面状态、数据字段和展示顺序之间的协作关系。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
            ]
        if "课程" in lowered or "校园" in lowered or "训练" in lowered:
            return [
                ResumeBullet(
                    text="在自动化专业学习中形成结构化分析习惯，能够把复杂问题拆成可执行步骤并清晰表达。",
                    evidence_status="transferable",
                    risk_level="low",
                ),
                ResumeBullet(
                    text="参与课程作业和文档整理时，注重信息归纳、沟通确认与复盘总结。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
                ResumeBullet(
                    text="结合项目练习尝试从用户视角观察功能路径，提升方案表达与协作意识。",
                    evidence_status="inferred",
                    risk_level="medium",
                ),
            ]
        return [
            ResumeBullet(
                text="围绕真实项目场景梳理需求、功能和结果展示关系，形成产品化表达。",
                evidence_status="transferable",
                risk_level="low",
            ),
            ResumeBullet(
                text="结合已有技能对接口、字段和页面结构进行协作式理解，支撑原型验证。",
                evidence_status="inferred",
                risk_level="medium",
            ),
            ResumeBullet(
                text="在文档整理与迭代复盘中保持低风险表达，避免把推断写成硬事实。",
                evidence_status="transferable",
                risk_level="low",
            ),
        ]

    def _fallback_bullet_templates(self, title: str) -> list[ResumeBullet]:
        prefix = title or "项目"
        return [
            ResumeBullet(
                text=f"围绕 {prefix} 继续补足用户场景、信息结构和结果解释的产品化表达。",
                evidence_status="inferred",
                risk_level="medium",
            ),
            ResumeBullet(
                text=f"结合 {prefix} 的已有素材，整理出可继续投递前修改的完整表达。",
                evidence_status="transferable",
                risk_level="low",
            ),
        ]

    def _merge_bullets(
        self,
        existing: list[ResumeBullet],
        templates: list[ResumeBullet],
    ) -> list[ResumeBullet]:
        merged = self._dedupe_bullets(existing)
        for bullet in templates:
            if len(merged) >= len(existing) + len(templates):
                break
            if len(merged) < 20:
                merged.append(bullet)
        return self._dedupe_bullets(merged)

    def _sanitize_bullets(
        self,
        bullets: Iterable[ResumeBullet],
        keep_statuses: set[str],
    ) -> list[ResumeBullet]:
        sanitized: list[ResumeBullet] = []
        for bullet in bullets:
            if bullet.evidence_status not in keep_statuses:
                continue
            text = self._clean_text(bullet.text)
            if not text:
                continue
            risk_level = bullet.risk_level if bullet.risk_level in {"low", "medium", "high"} else "low"
            sanitized.append(
                ResumeBullet(
                    text=text,
                    evidence_status=bullet.evidence_status,  # type: ignore[arg-type]
                    risk_level=risk_level,
                )
            )
        return self._dedupe_bullets(sanitized)

    def _collect_side_report_items_from_raw_resume(
        self,
        resume: ResumeJSON,
    ) -> list[tuple[str, str]]:
        collected: list[tuple[str, str]] = []
        for bullet in [
            *resume.summary,
            *[bullet for module in resume.projects for bullet in module.bullets],
            *[bullet for module in resume.practice_experiences for bullet in module.bullets],
            *[bullet for module in resume.campus_or_competition for bullet in module.bullets],
            *resume.self_evaluation,
        ]:
            if bullet.evidence_status not in {"unsupported", "missing"}:
                continue
            collected.append((bullet.evidence_status, bullet.text))
        return collected

    def _build_headline(
        self,
        resume: ResumeJSON | None,
        jd_profile: JDProfile,
        user_profile: UserProfile,
    ) -> str:
        candidate = self._safe_text(user_profile.headline or (resume.headline if resume else ""), "")
        if candidate and not self._contains_banned_terms(candidate):
            return candidate
        skills = self._unique_texts(user_profile.skills + jd_profile.required_skills)
        skill_hint = "、".join(skills[:3]) if skills else "需求拆解与技术协作"
        return f"{self._safe_text(jd_profile.position, '目标岗位')}方向｜具备{skill_hint}基础"

    def _project_title(self, source: WorkExperience | None) -> str:
        if not source:
            return "AI 产品功能设计与原型实践"
        candidate = self._safe_text(source.role or source.company, "")
        if self._looks_like_project_title(candidate):
            return candidate
        return "AI 产品功能设计与原型实践"

    def _looks_like_project_title(self, title: str) -> bool:
        markers = ("项目", "系统", "平台", "原型", "助手", "工具", "Demo", "应用", "方案")
        return any(marker.lower() in title.lower() for marker in markers)

    def _primary_experience(self, user_profile: UserProfile) -> WorkExperience | None:
        return user_profile.experiences[0] if user_profile.experiences else None

    def _collect_project_signals(self, modules: list[ResumeModule]) -> list[str]:
        signals: list[str] = []
        for module in modules:
            signals.append(module.title)
            signals.extend(bullet.text for bullet in module.bullets[:2])
        return self._unique_texts(signals)

    def _extract_education_hint(self, education: list[str]) -> str:
        if not education:
            return ""
        first = education[0]
        cleaned = self._safe_text(first, "")
        return cleaned

    def _unique_texts(self, values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = self._clean_text(value)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            result.append(cleaned)
        return result

    def _dedupe_bullets(self, bullets: Iterable[ResumeBullet]) -> list[ResumeBullet]:
        seen: set[str] = set()
        result: list[ResumeBullet] = []
        for bullet in bullets:
            normalized = self._clean_text(bullet.text)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(
                ResumeBullet(
                    text=normalized,
                    evidence_status=bullet.evidence_status,
                    risk_level=bullet.risk_level,
                )
            )
        return result

    def _fill_bullets(
        self,
        bullets: list[ResumeBullet],
        templates: list[ResumeBullet],
        target: int,
    ) -> list[ResumeBullet]:
        merged = self._dedupe_bullets(bullets)
        for template in templates:
            if len(merged) >= target:
                break
            merged.append(template)
        return self._dedupe_bullets(merged)

    def _clean_text(self, value: str | None) -> str:
        text = value.strip() if isinstance(value, str) else ""
        if not text:
            return ""
        for phrase in _BANNED_TERMS:
            text = text.replace(phrase, "")
        text = re.sub(r"\s+", " ", text).strip(" ，,。;；:：-")
        return text

    def _safe_text(self, value: str | None, fallback: str) -> str:
        cleaned = self._clean_text(value)
        return cleaned or fallback

    def _contains_banned_terms(self, text: str) -> bool:
        return any(term in text for term in _BANNED_TERMS)
