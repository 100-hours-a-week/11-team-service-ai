
import pytest
from pipelines.applicant_evaluation.domain.models.document import ParsedDoc, ApplicantDocuments, FileInfo

class TestParsedDoc:
    def test_analyzable_condition_length(self):
        """텍스트 길이가 50자를 초과해야 분석 가능"""
        # Case 1: 50 chars (False)
        short_text = "A" * 50
        doc = ParsedDoc(doc_type="RESUME", text=short_text)
        assert doc.is_analyzable() is False

        # Case 2: 51 chars (True)
        long_text = "A" * 51
        doc = ParsedDoc(doc_type="RESUME", text=long_text)
        assert doc.is_analyzable() is True

    def test_analyzable_condition_validity(self):
        """is_valid 플래그가 False면 길이와 상관없이 분석 불가"""
        text = "A" * 100
        doc = ParsedDoc(doc_type="RESUME", text=text, is_valid=False)
        assert doc.is_analyzable() is False

    def test_analyzable_condition_whitespace(self):
        """공백 제외 길이가 기준을 넘어야 함"""
        # 100 chars but only spaces (strip().length == 0)
        text = " " * 100
        doc = ParsedDoc(doc_type="RESUME", text=text)
        assert doc.is_analyzable() is False

        # 50 chars + spaces
        text_with_space = ("A" * 50) + (" " * 10)
        doc = ParsedDoc(doc_type="RESUME", text=text_with_space)
        assert doc.is_analyzable() is False  # stripped length is 50 -> False


class TestApplicantDocuments:
    @pytest.fixture
    def resume_file(self):
        return FileInfo(file_path="path/to/resume", file_type="RESUME")
        
    @pytest.fixture
    def portfolio_file(self):
        return FileInfo(file_path="path/to/portfolio", file_type="PORTFOLIO")

    @pytest.fixture
    def valid_parsed(self):
        return ParsedDoc(doc_type="RESUME", text="A" * 60)

    def test_is_ready_no_files(self):
        """제출된 파일이 아예 없으면 분석 준비 완료(할 게 없음)로 간주"""
        docs = ApplicantDocuments()
        assert docs.is_ready_for_analysis() is True
        assert docs.get_missing_parsed_types() == []

    def test_is_ready_file_exists_but_not_parsed(self, resume_file):
        """파일은 있는데 파싱 데이터가 없으면 Not Ready"""
        docs = ApplicantDocuments(resume_file=resume_file, parsed_resume=None)
        assert docs.is_ready_for_analysis() is False
        assert docs.get_missing_parsed_types() == ["RESUME"]

    def test_is_ready_file_exists_and_parsed_valid(self, resume_file, valid_parsed):
        """파일도 있고 파싱 데이터도 유효하면 Ready"""
        docs = ApplicantDocuments(resume_file=resume_file, parsed_resume=valid_parsed)
        assert docs.is_ready_for_analysis() is True
        assert docs.get_missing_parsed_types() == []

    def test_is_ready_parsed_but_invalid(self, resume_file):
        """파싱 데이터가 있지만 유효하지 않으면(너무 짧음) Not Ready"""
        invalid_parsed = ParsedDoc(doc_type="RESUME", text="Short")
        docs = ApplicantDocuments(resume_file=resume_file, parsed_resume=invalid_parsed)
        
        # 주의: 현재 로직상 '분석 불가능'도 '준비 안 됨'으로 취급하여 재파싱 등을 유도할 수 있음
        # 혹은 '준비는 됐으나 내용 미달'로 볼 수도 있음. 코드(document.py) 로직에 따르면 False임.
        assert docs.is_ready_for_analysis() is False
        assert docs.get_missing_parsed_types() == ["RESUME"]

    def test_missing_types_multiple(self, resume_file, portfolio_file, valid_parsed):
        """이력서는 준비됐지만 포트폴리오가 없을 때"""
        docs = ApplicantDocuments(
            resume_file=resume_file, 
            parsed_resume=valid_parsed,
            portfolio_file=portfolio_file,
            parsed_portfolio=None
        )
        
        assert docs.is_ready_for_analysis() is False
        # 순서 중요하지 않다면 set 비교 권장, 여기선 리스트
        assert docs.get_missing_parsed_types() == ["PORTFOLIO"]
