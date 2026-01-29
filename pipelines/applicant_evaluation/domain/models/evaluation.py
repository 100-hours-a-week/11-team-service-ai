from dataclasses import dataclass

@dataclass
class CompetencyResult:
    """개별 역량 평가 결과 (AI 분석 결과 1건)"""
    name: str            # 역량 항목명 (criteria_name)
    score: float         # 역량 점수
    description: str     # 역량 평가 상세 (reason)

    # 점수 유효성 검증 로직 구현
    def validate_score(self):
        if not (0 <= self.score <= 100):
            raise ValueError("Score must be between 0 and 100")

