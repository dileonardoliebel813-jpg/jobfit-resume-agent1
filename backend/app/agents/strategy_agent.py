from app.schemas.jd_schema import JDProfile
from app.schemas.match_schema import MatchAnalysis
from app.schemas.profile_schema import UserProfile


class StrategyAgent:
    def plan(
        self,
        jd_profile: JDProfile,
        user_profile: UserProfile,
        match: MatchAnalysis,
    ) -> list[str]:
        notes = [
            f"目标岗位为 {jd_profile.position}，简历只能使用候选人已提供经历。",
            "优先展示与 JD 直接匹配且有证据支撑的项目事实。",
        ]
        if match.gaps:
            notes.append(f"以下 JD 要求证据较弱，应放入 side_report：{', '.join(match.gaps[:6])}。")
        if not user_profile.experiences:
            notes.append("候选人当前没有可直接写入的经历素材，生成内容将转为完整草稿和待确认说明。")
        if not user_profile.name.strip():
            notes.append("候选人姓名尚未明确，生成内容顶部将使用通用称呼。")
        return notes[:5]
