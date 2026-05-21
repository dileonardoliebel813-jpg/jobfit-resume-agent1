from fastapi.testclient import TestClient


def _jd_profile() -> dict:
    return {
        "position": "AI 产品经理",
        "job_level": "初级",
        "job_type": "全职",
        "hard_requirements": ["PRD撰写", "AI产品设计"],
        "core_tasks": ["推进研发协作", "数据指标分析"],
        "required_skills": ["SQL", "RAG"],
        "preferred_experience": ["推荐策略项目经验"],
        "hidden_preferences": ["结果导向"],
        "resume_strategy": {
            "must_highlight": ["真实项目证据"],
            "should_weaken": ["无证据的泛泛表述"],
            "tone": "真实、保守、证据导向",
        },
    }


def _education_only_profile() -> dict:
    return {
        "name": "候选人",
        "headline": "本科在读",
        "skills": [],
        "experiences": [],
        "education": ["自动化本科"],
    }


def _partial_profile() -> dict:
    return {
        "name": "候选人",
        "headline": "有产品课程项目经验",
        "skills": ["SQL", "Figma"],
        "experiences": [
            {
                "company": "课程项目",
                "role": "产品设计负责人",
                "duration": "2025",
                "highlights": [
                    "负责PRD撰写和原型设计，使用Figma完成流程页面。",
                    "使用SQL分析用户行为数据并梳理指标口径。",
                ],
                "skills": ["PRD撰写", "SQL", "Figma"],
            }
        ],
        "education": ["自动化本科"],
    }


def test_match_diagnose_not_recommended_for_education_only(client: TestClient) -> None:
    response = client.post(
        "/api/v1/match/diagnose",
        json={
            "jd_profile": _jd_profile(),
            "user_profile": _education_only_profile(),
            "raw_profile_text": "自动化本科在读，暂未提供项目或实习经历。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generation_recommendation"] == "not_recommended"
    assert body["coverage_score"] == 0
    assert body["missing_evidence_questions"]


def test_match_diagnose_respects_user_confirmed_absent(client: TestClient) -> None:
    response = client.post(
        "/api/v1/match/diagnose",
        json={
            "jd_profile": _jd_profile(),
            "user_profile": _partial_profile(),
            "raw_profile_text": "有课程项目，但没有RAG相关经历。",
            "user_confirmed_absent_requirements": ["RAG"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    rag_item = next(item for item in body["evidence_items"] if item["requirement"] == "RAG")
    assert rag_item["status"] == "user_confirmed_absent"
    assert "RAG" in body["safe_resume_strategy"]["must_not_claim"]


def test_match_diagnose_finds_partial_true_evidence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/match/diagnose",
        json={
            "jd_profile": _jd_profile(),
            "user_profile": _partial_profile(),
            "raw_profile_text": "负责PRD撰写、Figma原型和SQL指标分析。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["coverage_score"] > 0
    assert body["generation_recommendation"] in {"ready", "needs_more_info"}
    assert "PRD撰写" in body["safe_resume_strategy"]["can_write"]
