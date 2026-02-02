from dataclasses import dataclass
from typing import Optional


@dataclass
class FileInfo:
    """파일명, 경로 등 원본 파일 메타데이터"""

    file_path: str
    file_type: str  # "RESUME" or "PORTFOLIO"


@dataclass
class ParsedDoc:
    """분석 가능한 상태로 추출된 텍스트 데이터"""

    doc_type: str
    text: str
    is_valid: bool = True

    def is_analyzable(self) -> bool:
        """
        텍스트가 충분히 존재하고 유효한지 검사
        TODO: 최소 길이 체크, 깨진 글자 체크 등 로직 구현
        """
        return self.is_valid and len(self.text.strip()) > 50


@dataclass
class ApplicantDocuments:
    """한 지원자의 특정 공고에 대한 전체 제출 서류"""

    resume_file: Optional[FileInfo] = None
    portfolio_file: Optional[FileInfo] = None

    parsed_resume: Optional[ParsedDoc] = None
    parsed_portfolio: Optional[ParsedDoc] = None

    def has_all_files(self) -> bool:
        """이력서와 포트폴리오 파일 원본이 모두 존재하는지 확인"""
        # TODO: 필수 서류 조건에 따라 로직 구체화 (둘 다 필수인지 등)
        return self.resume_file is not None and self.portfolio_file is not None

    def is_ready_for_analysis(self) -> bool:
        """
        분석 가능한 텍스트 데이터가 모두 준비되었는지 확인.
        원본 파일이 있으면 파싱된 데이터도 있어야 함.
        """
        # 파일이 있는데 파싱 데이터가 없다면 False 반환
        if self.resume_file and (
            not self.parsed_resume or not self.parsed_resume.is_analyzable()
        ):
            return False

        if self.portfolio_file and (
            not self.parsed_portfolio or not self.parsed_portfolio.is_analyzable()
        ):
            return False

        return True

    def get_missing_parsed_types(self) -> list[str]:
        """
        분석을 위해 텍스트 추출이 필요한 파일 타입 목록 반환
        """
        missing = []
        if self.resume_file and (
            not self.parsed_resume or not self.parsed_resume.is_analyzable()
        ):
            missing.append("RESUME")

        if self.portfolio_file and (
            not self.parsed_portfolio or not self.parsed_portfolio.is_analyzable()
        ):
            missing.append("PORTFOLIO")

        return missing
