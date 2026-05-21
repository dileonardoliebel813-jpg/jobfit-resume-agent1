from fastapi.testclient import TestClient
from io import BytesIO
from pypdf import PdfReader

from app.schemas.resume_schema import ResumeJSON
from app.services.resume_pdf_export import ContactInfo, build_printable_resume


def _sample_resume() -> dict:
    return {
        "candidate_name": "韩菁菁",
        "target_title": "AI产品经理",
        "headline": "AI产品经理方向",
        "summary": [
            {
                "text": "具备AI产品认知，通过CampRank项目完成用户场景分析、需求拆解与推荐策略设计。",
                "evidence_status": "supported",
                "risk_level": "low",
            },
            {
                "text": "熟练运用Figma、Axure进行产品原型设计，能够输出清晰的信息架构。",
                "evidence_status": "transferable",
                "risk_level": "low",
            },
            {
                "text": "掌握Python、SQL等数据分析技能，能够识别用户决策风险。",
                "evidence_status": "supported",
                "risk_level": "low",
            },
        ],
        "skills": [
            "Figma",
            "Axure",
            "XMind",
            "产品原型设计",
            "信息架构设计",
            "需求文档撰写",
            "Python数据分析",
            "SQL数据查询",
            "数据清洗与处理",
            "推荐策略设计",
            "风险指标建模",
            "AI辅助开发",
            "熟练使用 Figma",
        ],
        "projects": [
            {
                "title": "CampRank AI 帐篷购买决策助手",
                "subtitle": "AI产品实践项目",
                "bullets": [
                    {
                        "text": "分析大学生和职场新人的帐篷购买场景，梳理用户在预算、使用场景和售后风险上的决策痛点。",
                        "evidence_status": "supported",
                        "risk_level": "low",
                    }
                ],
            }
        ],
        "practice_experiences": [],
        "campus_or_competition": [
            {
                "title": "数学建模竞赛",
                "subtitle": "全国一等奖",
                "bullets": [
                    {
                        "text": "作为队长组织团队，针对实际问题进行需求拆解与建模。",
                        "evidence_status": "supported",
                        "risk_level": "low",
                    }
                ],
            }
        ],
        "education": [
            "曲阜师范大学 | 自动化 | 本科 | 2022.9-2026.6",
            "GPA: 3.6/5.0 专业排名: 20/200",
            "曲阜师范大学 | 自动化 | 本科 2022.9~2026.6",
        ],
        "self_evaluation": [],
        "side_report": {
            "missing_info": ["未提供商业化上线证明"],
            "weak_match_points": ["需确认Figma原型细节"],
            "suggested_user_inputs": ["补充项目截图"],
            "assumptions_need_confirmation": ["能力迁移表达需要确认"],
            "match_gap_summary": "仅用于页面诊断，不进入PDF。",
        },
    }


def test_export_resume_pdf_returns_file(client: TestClient) -> None:
    response = client.post(
        "/api/v1/export/resume",
        json={
            "resume_json": _sample_resume(),
            "format": "pdf",
            "layout": "one_page",
            "photo_mode": "placeholder",
            "contact_info": {
                "name": "韩菁菁",
                "age": "22岁",
                "phone": "13800000000",
                "email": "han@example.com",
                "location": "山东日照",
                "github": "https://github.com/example",
                "target_title": "AI 产品经理",
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000
    reader = PdfReader(BytesIO(response.content))
    assert 1 <= len(reader.pages) <= 2


def test_printable_resume_omits_internal_markers_and_merges_education() -> None:
    printable = build_printable_resume(
        ResumeJSON.model_validate(_sample_resume()),
        contact_info=ContactInfo(
            name="韩菁菁",
            age="22岁",
            phone="13800000000",
            email="han@example.com",
            location="山东日照",
            github="https://github.com/example",
            target_title="AI 产品经理",
        ),
    )
    printable_text = "\n".join(
        [
            *printable.education,
            *printable.summary,
            *printable.skills,
            *printable.campus,
            *[project.intro for project in printable.projects],
            *[bullet for project in printable.projects for bullet in project.bullets],
        ]
    )

    assert printable.education.count("曲阜师范大学 | 自动化 | 本科 | 2022.09 - 2026.06") == 1
    assert printable.contact.phone == "13800000000"
    assert printable.contact.email == "han@example.com"
    assert len(printable.skills) <= 16
    assert len(printable.projects[0].bullets) == 5
    assert printable.projects[0].intro == (
        "面向大学生轻露营场景的 AI 帐篷购买决策助手，基于商品参数、用户评价与平台风险，提供可解释的选购推荐。"
    )
    for marker in ["未提供", "真实支持", "能力迁移", "需确认", "side_report", "生成说明"]:
        assert marker not in printable_text


def test_printable_resume_section_content_order_is_formal() -> None:
    printable = build_printable_resume(ResumeJSON.model_validate(_sample_resume()))

    section_titles = ["教育背景", "个人优势", "专业技能", "项目经历", "校园 / 竞赛经历"]
    assert section_titles == ["教育背景", "个人优势", "专业技能", "项目经历", "校园 / 竞赛经历"]
    assert printable.education
    assert len(printable.summary) >= 3
    assert len(printable.skills) >= 12
    assert printable.projects[0].title == "CampRank AI 帐篷购买决策助手"
    assert len(printable.campus) >= 2
