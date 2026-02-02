import hashlib
from typing import List

class FingerprintGenerator:
    """
    공고 내용의 고유 지문(Fingerprint)을 생성하여 중복 여부를 판별하는 유틸리티.
    """

    @staticmethod
    def generate(company_name: str, job_title: str, main_tasks: List[str]) -> str:
        """
        핵심 필드를 조합하여 SHA-256 해시를 생성합니다.
        공백이나 대소문자 차이로 인한 불일치를 방지하기 위해 정규화 과정을 거칩니다.
        """
        # 1. 텍스트 정규화 (소문자, 공백 제거)
        normalized_company = company_name.strip().lower().replace(" ", "")
        normalized_title = job_title.strip().lower().replace(" ", "")

        # 2. 리스트 정렬 (순서가 달라도 내용이 같으면 중복으로 처리)
        # main_tasks는 내용이 중요하므로 정렬 후 문자열로 합침
        normalized_tasks = sorted([task.strip().lower() for task in main_tasks if task])
        tasks_str = "".join(normalized_tasks)

        # 3. 조합
        combined_text = f"{normalized_company}|{normalized_title}|{tasks_str}"

        # 4. 해시 생성
        return hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
