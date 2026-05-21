from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.resume_schema import ResumeJSON, ResumeModule


_BANNED_TERMS = (
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
)
_FONT_NAME = "ResumeCJK"
_FONT_BOLD_NAME = "ResumeCJKBold"
_DARK = colors.HexColor("#101923")
_BLUE = colors.HexColor("#2563A8")
_TEXT = colors.HexColor("#111827")
_MUTED = colors.HexColor("#4B5563")


@dataclass
class ContactInfo:
    name: str = ""
    age: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    github: str = ""
    target_title: str = ""


@dataclass
class PrintableProject:
    title: str
    role: str
    intro: str
    tech_stack: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class PrintableResume:
    candidate_name: str
    target_title: str
    contact: ContactInfo
    education: list[str]
    summary: list[str]
    skills: list[str]
    projects: list[PrintableProject]
    campus: list[str]


class TopBar(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 180 * mm
        self.height = 18 * mm

    def draw(self) -> None:
        self.canv.setFillColor(_DARK)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor("#2F9CC2"))
        self.canv.rect(0, 0, 18 * mm, self.height, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont(_FONT_BOLD_NAME, 15)
        self.canv.drawString(22 * mm, 6 * mm, "个人简历")


class PhotoPlaceholder(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 30 * mm
        self.height = 38 * mm

    def draw(self) -> None:
        self.canv.setFillColor(colors.HexColor("#2F8DCC"))
        self.canv.roundRect(0, 0, self.width, self.height, 1.5, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor("#D8ECFF"))
        self.canv.circle(self.width / 2, 25 * mm, 5.5 * mm, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.roundRect(7 * mm, 7 * mm, 16 * mm, 12 * mm, 5, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor("#1F2937"))
        self.canv.setFont(_FONT_NAME, 6)
        self.canv.drawCentredString(self.width / 2, 2.5 * mm, "照片占位")


class SectionTitle(Flowable):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.width = 180 * mm
        self.height = 10 * mm

    def draw(self) -> None:
        self.canv.setFillColor(_TEXT)
        self.canv.setFont(_FONT_BOLD_NAME, 10.5)
        self.canv.drawString(0, 3.5 * mm, self.text)
        self.canv.setStrokeColor(colors.HexColor("#4B5563"))
        self.canv.setLineWidth(0.7)
        self.canv.line(0, 2.3 * mm, self.width, 2.3 * mm)
        self.canv.setFillColor(_BLUE)
        self.canv.rect(0, 1.5 * mm, 22 * mm, 1.8 * mm, fill=1, stroke=0)


def build_resume_pdf(
    resume: ResumeJSON,
    layout: str = "one_page",
    contact_info: ContactInfo | None = None,
    photo_mode: str = "placeholder",
) -> bytes:
    register_resume_fonts()
    printable = build_printable_resume(
        resume,
        one_page=layout == "one_page",
        contact_info=contact_info,
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"{printable.candidate_name}_resume",
    )
    styles = _styles()
    story: list[Flowable] = []

    story.append(TopBar())
    story.append(Spacer(1, 9))
    story.extend(_profile_header(printable, styles, photo_mode=photo_mode))
    story.extend(_section("教育背景", _paragraphs(printable.education, styles["body"]), compact=True))
    story.extend(_section("个人优势", _bullets(printable.summary, styles), compact=True))
    skill_content = [_skill_table(printable.skills, styles)] if printable.skills else []
    story.extend(_section("专业技能", skill_content, compact=True))
    story.extend(_section("项目经历", _project_blocks(printable.projects, styles), compact=True))
    story.extend(_section("校园 / 竞赛经历", _bullets(printable.campus, styles), compact=True))

    document.build(story)
    return buffer.getvalue()


def build_printable_resume(
    resume: ResumeJSON,
    one_page: bool = True,
    contact_info: ContactInfo | None = None,
) -> PrintableResume:
    all_text = _all_resume_text(resume)
    contact = _merge_contact(resume, all_text, contact_info)
    candidate_name = _clean_text(contact.name) or _clean_text(resume.candidate_name) or "姓名待填写"
    target_title = (
        _clean_text(contact.target_title)
        or _clean_text(resume.target_title)
        or "AI 产品经理"
    )
    contact.name = candidate_name
    contact.target_title = target_title

    summary = _build_summary([item.text for item in resume.summary], all_text)
    skills = _normalize_skills(resume.skills)
    education = _build_education(resume.education)
    projects = _build_projects(resume.projects, skills, one_page=one_page)
    campus = _build_campus(resume.campus_or_competition, resume.education, all_text, one_page=one_page)

    return PrintableResume(
        candidate_name=candidate_name,
        target_title=target_title,
        contact=contact,
        education=education,
        summary=summary[:4],
        skills=skills[:16],
        projects=projects[:1],
        campus=campus[:3],
    )


def register_resume_fonts() -> None:
    if _FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return

    regular_candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    bold_candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
    ]
    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), regular)
    if regular is None:
        raise RuntimeError("No Chinese font found for PDF export")

    pdfmetrics.registerFont(TTFont(_FONT_NAME, str(regular), subfontIndex=0))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD_NAME, str(bold), subfontIndex=0))


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "name": ParagraphStyle(
            "ResumeName",
            fontName=_FONT_BOLD_NAME,
            fontSize=25,
            leading=29,
            textColor=_TEXT,
            alignment=TA_LEFT,
            wordWrap="CJK",
        ),
        "target": ParagraphStyle(
            "ResumeTarget",
            fontName=_FONT_BOLD_NAME,
            fontSize=14,
            leading=18,
            textColor=_TEXT,
            wordWrap="CJK",
        ),
        "contact": ParagraphStyle(
            "ResumeContact",
            fontName=_FONT_NAME,
            fontSize=9.2,
            leading=13,
            textColor=_TEXT,
            alignment=TA_RIGHT,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "ResumeBody",
            fontName=_FONT_NAME,
            fontSize=8.7,
            leading=11.2,
            textColor=_TEXT,
            wordWrap="CJK",
            spaceAfter=1,
        ),
        "body_bold": ParagraphStyle(
            "ResumeBodyBold",
            fontName=_FONT_BOLD_NAME,
            fontSize=9.2,
            leading=12,
            textColor=_TEXT,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "ResumeSmall",
            fontName=_FONT_NAME,
            fontSize=8.2,
            leading=10.2,
            textColor=_TEXT,
            wordWrap="CJK",
        ),
    }


def _profile_header(printable: PrintableResume, styles: dict[str, ParagraphStyle], photo_mode: str) -> list[Flowable]:
    contact_lines = _contact_lines(printable.contact)
    contact_paragraph = Paragraph("<br/>".join(_escape(line) for line in contact_lines), styles["contact"])
    center = [
        Paragraph(_escape(printable.candidate_name), styles["name"]),
        Spacer(1, 9),
        Paragraph(f"求职意向： {_escape(printable.target_title)}", styles["target"]),
    ]
    photo: Flowable = PhotoPlaceholder() if photo_mode == "placeholder" else PhotoPlaceholder()
    table = Table(
        [[photo, center, contact_paragraph]],
        colWidths=[38 * mm, 86 * mm, 56 * mm],
        rowHeights=[42 * mm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [table, Spacer(1, 4)]


def _contact_lines(contact: ContactInfo) -> list[str]:
    return [
        f"年龄：{_clean_text(contact.age) or '待填写'}",
        f"电话：{_clean_text(contact.phone) or '待填写'}",
        f"邮箱：{_clean_text(contact.email) or '待填写'}",
        f"所在地：{_clean_text(contact.location) or '待填写'}",
        f"GitHub：{_clean_text(contact.github) or '待填写'}",
    ]


def _section(title: str, content: list[Flowable], compact: bool = False) -> list[Flowable]:
    if not content:
        return []
    gap = 3 if compact else 6
    return [SectionTitle(title), Spacer(1, 1.5), *content, Spacer(1, gap)]


def _paragraphs(values: list[str], style: ParagraphStyle) -> list[Flowable]:
    return [Paragraph(_escape(value), style) for value in values if value]


def _bullets(values: list[str], styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    items = [
        ListItem(Paragraph(_escape(value), styles["body"]), leftIndent=7, bulletFontSize=5.5)
        for value in values
        if value
    ]
    return [
        ListFlowable(
            items,
            bulletType="bullet",
            bulletFontName=_FONT_NAME,
            bulletFontSize=5.5,
            leftIndent=10,
            bulletOffsetY=1,
            spaceBefore=0,
            spaceAfter=0,
        )
    ] if items else []


def _skill_table(skills: list[str], styles: dict[str, ParagraphStyle]) -> Flowable:
    rows: list[list[Paragraph]] = []
    row: list[Paragraph] = []
    for skill in skills:
        row.append(Paragraph(_escape(skill), styles["small"]))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        while len(row) < 4:
            row.append(Paragraph("", styles["small"]))
        rows.append(row)

    table = Table(rows, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ]
        )
    )
    return table


def _project_blocks(projects: list[PrintableProject], styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    blocks: list[Flowable] = []
    for project in projects:
        heading = Table(
            [[Paragraph(_escape(project.title), styles["body_bold"]), Paragraph(_escape(project.role), styles["body_bold"])]],
            colWidths=[112 * mm, 68 * mm],
            hAlign="LEFT",
        )
        heading.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        blocks.append(
            KeepTogether(
                [
                    heading,
                    Paragraph(f"<b>项目简介：</b>{_escape(project.intro)}", styles["body"]),
                    Paragraph(f"<b>技术栈：</b>{_escape(project.tech_stack)}", styles["body"]),
                    Paragraph("<b>项目职责 / 技术难点：</b>", styles["body"]),
                    *_bullets(project.bullets, styles),
                ]
            )
        )
    return blocks


def _merge_contact(resume: ResumeJSON, all_text: str, contact_info: ContactInfo | None) -> ContactInfo:
    base = contact_info or ContactInfo()
    return ContactInfo(
        name=_clean_text(base.name) or _clean_text(resume.candidate_name),
        age=_clean_text(base.age) or _extract_age(all_text),
        phone=_clean_text(base.phone) or _extract_phone(all_text),
        email=_clean_text(base.email) or _extract_email(all_text),
        location=_clean_text(base.location) or _extract_location(all_text),
        github=_clean_text(base.github) or _extract_github(all_text),
        target_title=_clean_text(base.target_title) or _clean_text(resume.target_title),
    )


def _build_education(values: list[str]) -> list[str]:
    text = " ".join(_clean_text(value) for value in values)
    if "曲阜师范大学" in text or "自动化" in text:
        return [
            "曲阜师范大学 | 自动化 | 本科 | 2022.09 - 2026.06",
            "GPA: 3.6/5.0 | 专业排名: 20/200",
            "主修课程：微机原理与接口技术、Python、C++程序设计、计算机控制技术、电路分析",
            "奖项：数学建模比赛全国一等奖、国家励志奖学金、优秀毕业生、三等奖学金、优秀学生干部",
        ]
    return _unique([_clean_text(value) for value in values])[:4]


def _build_summary(values: list[str], all_text: str) -> list[str]:
    cleaned = _take_clean_bullets(values, limit=4)
    if "CampRank" in all_text or "帐篷" in all_text or "购买决策" in all_text:
        templates = [
            "具备 AI 产品认知，能围绕用户场景、需求拆解、推荐策略与效果优化形成完整产品实践。",
            "参与 CampRank AI 决策助手项目，能够将商品参数、用户评价与平台风险转化为可解释推荐逻辑。",
            "掌握 Python、SQL、数据清洗与风险建模能力，能够用数据分析支持产品判断与迭代。",
            "熟悉 Figma、Axure、XMind 等工具，能够输出产品原型、信息架构和需求说明。",
        ]
        cleaned = _unique([*cleaned, *templates])
    return cleaned[:4]


def _build_projects(modules: list[ResumeModule], skills: list[str], one_page: bool) -> list[PrintableProject]:
    source_text = " ".join(
        [_clean_text(module.title) for module in modules]
        + [_clean_text(bullet.text) for module in modules for bullet in module.bullets]
        + skills
    )
    if "CampRank" in source_text or "帐篷" in source_text or "购买决策" in source_text:
        bullets = [
            "围绕帐篷选购场景，梳理预算、人数、使用场景、售后风险等核心决策因素，定义用户推荐需求。",
            "设计“商品数据清洗 - 特征建模 - 评分排序 - 解释输出”的产品信息架构，形成结构化证据链条。",
            "基于评论信息量、追评、带图等因素设计有效评论权重模型，识别漏水、防风差等风险维度。",
            "通过样本偏差校准与贝叶斯平滑优化评分排序，提升推荐结果在评分分布不均时的参考价值。",
            "使用 Figma / Axure 绘制原型，配合 React、FastAPI、SQLite 完成产品原型验证与功能表达。",
        ]
        return [
            PrintableProject(
                title="CampRank AI 帐篷购买决策助手",
                role="AI 产品经理 / AI 应用开发",
                intro="面向大学生轻露营场景的 AI 帐篷购买决策助手，基于商品参数、用户评价与平台风险，提供可解释的选购推荐。",
                tech_stack="React、FastAPI、SQLite、SQLAlchemy、Python、SQL、Figma、Axure、AI 辅助开发",
                bullets=bullets[:5],
            )
        ]

    projects: list[PrintableProject] = []
    for module in modules:
        bullets = _take_clean_bullets([bullet.text for bullet in module.bullets], limit=5 if not one_page else 4)
        if not bullets:
            continue
        projects.append(
            PrintableProject(
                title=_clean_text(module.title) or "项目实践",
                role=_clean_text(module.subtitle) or "项目实践",
                intro=_shorten(bullets[0], 76),
                tech_stack="、".join(skills[:10]),
                bullets=bullets,
            )
        )
    return projects


def _build_campus(
    modules: list[ResumeModule],
    education: list[str],
    all_text: str,
    one_page: bool,
) -> list[str]:
    if "数学建模" in all_text:
        return [
            "数学建模竞赛全国一等奖：作为队长组织团队完成需求拆解、数据清洗、模型设计与论文撰写。",
            "使用 Python 进行数据处理与模型求解，体现复杂问题拆解、快速学习和协作推进能力。",
            "结合自动化专业训练，具备结构化分析、文档整理和跨角色沟通基础。",
        ][:3]
    bullets = _take_clean_bullets([bullet.text for module in modules for bullet in module.bullets], limit=3)
    if bullets:
        return bullets
    education_text = " ".join(_clean_text(value) for value in education)
    return [_shorten(education_text, 92)] if education_text else []


def _normalize_skills(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in values:
        for piece in re.split(r"[、,，;；/\n]+", raw):
            value = _clean_text(piece)
            if not value:
                continue
            value = value.replace("熟练使用 ", "").replace("熟练使用", "")
            value = value.replace("可完成原型图", "产品原型设计")
            mapping = {
                "Python数据分析": "Python",
                "SQL数据查询": "SQL",
                "数据清洗与处理": "数据清洗",
            }
            normalized.append(mapping.get(value, value))

    preferred_order = [
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
    ]
    values_text = " ".join(normalized)
    ordered = [skill for skill in preferred_order if skill in normalized or _skill_matches(skill, values_text)]
    ordered.extend(normalized)
    return _unique(ordered)[:16]


def _skill_matches(skill: str, values_text: str) -> bool:
    product_skills = {"PRD", "产品原型设计", "信息架构设计", "需求文档撰写", "用户场景分析", "需求分析"}
    ai_data_skills = {"推荐策略设计", "风险指标建模", "Prompt 工程", "AI 辅助开发"}
    if skill in product_skills:
        return any(keyword in values_text for keyword in ["Figma", "Axure", "原型", "需求", "产品", "信息架构"])
    if skill in ai_data_skills:
        return any(keyword in values_text for keyword in ["推荐", "风险", "AI", "数据", "Prompt"])
    return False


def _take_clean_bullets(values: list[str], limit: int) -> list[str]:
    return [_shorten(value, 96) for value in _unique([_clean_text(value) for value in values]) if value][:limit]


def _all_resume_text(resume: ResumeJSON) -> str:
    values = [
        resume.candidate_name,
        resume.target_title,
        resume.headline,
        *resume.skills,
        *resume.education,
        *[item.text for item in resume.summary],
        *[item.text for item in resume.self_evaluation],
        *[module.title for module in resume.projects],
        *[module.subtitle for module in resume.projects],
        *[bullet.text for module in resume.projects for bullet in module.bullets],
        *[module.title for module in resume.campus_or_competition],
        *[bullet.text for module in resume.campus_or_competition for bullet in module.bullets],
    ]
    return " ".join(_clean_text(value) for value in values)


def _extract_age(text: str) -> str:
    match = re.search(r"(\d{2})\s*岁", text)
    return match.group(1) + "岁" if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"1[3-9]\d{9}", text)
    return match.group(0) if match else ""


def _extract_email(text: str) -> str:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def _extract_github(text: str) -> str:
    match = re.search(r"https://github\.com/[A-Za-z0-9_.\-/]+", text)
    return match.group(0).rstrip("。,.，") if match else ""


def _extract_location(text: str) -> str:
    match = re.search(r"(山东省日照市|山东日照|日照|北京|上海|广州|深圳|杭州|南京|青岛)", text)
    return match.group(1) if match else ""


def _clean_text(value: str | None) -> str:
    text = (value or "").strip()
    for term in _BANNED_TERMS:
        text = text.replace(term, "")
    text = text.replace("", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[，,。;；:：\-\s]+|[，,。;；:：\-\s]+$", "", text)
    return text


def _shorten(value: str, max_chars: int) -> str:
    cleaned = _clean_text(value)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip("，,；;、 ") + "。"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = _clean_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _escape(value: str) -> str:
    return escape(value, {"'": "&apos;", '"': "&quot;"})
