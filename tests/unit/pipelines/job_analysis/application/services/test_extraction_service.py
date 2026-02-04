import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date

from pipelines.job_analysis.application.services.extraction_service import (
    JobExtractionService,
)
from pipelines.job_analysis.domain.interface.crawler import WebCrawler
from pipelines.job_analysis.domain.interface.extractor import JobDataExtractor
from pipelines.job_analysis.domain.models.job_data import (
    ExtractedJobData,
    EvaluationCriteriaItem,
)
from shared.schema.job_posting import JobPostingAnalyzeResponse


@pytest.fixture
def mock_crawler():
    return Mock(spec=WebCrawler)


@pytest.fixture
def mock_extractor():
    return Mock(spec=JobDataExtractor)


@pytest.fixture
def service(mock_crawler, mock_extractor):
    return JobExtractionService(crawler=mock_crawler, extractor=mock_extractor)


@pytest.mark.asyncio
async def test_extract_job_data_success(service, mock_crawler, mock_extractor):
    # Given
    url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123"
    raw_text = "<html><body>" + "Some Content " * 10 + "</body></html>"
    extracted_data = ExtractedJobData(
        company_name="Test Company",
        job_title="Python Developer",
        main_tasks=["Coding", "Testing"],
        tech_stacks=["Python", "Django"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        ai_summary="Looking for Python Dev",
        evaluation_criteria=[
            EvaluationCriteriaItem(name="Skill", description="Python Expert")
        ],
    )

    # Mocking behaviors
    mock_crawler.fetch.return_value = raw_text
    mock_extractor.extract = AsyncMock(return_value=extracted_data)

    # When
    response = await service.extract_job_data(url)

    # Then
    mock_crawler.fetch.assert_called_once_with(url)
    mock_extractor.extract.assert_awaited_once_with(raw_text)

    assert isinstance(response, JobPostingAnalyzeResponse)
    assert response.company_name == "Test Company"
    assert response.job_title == "Python Developer"
    assert response.required_skills == ["Python", "Django"]
    assert response.recruitment_period.start_date == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_extract_job_data_invalid_url(service, mock_crawler):
    # Given
    # Given
    url = "https://www.google.com/search?q=job"  # Not Saramin, Not Wanted

    # When & Then
    with pytest.raises(ValueError, match="사람인.*원티드.*지원"):
        await service.extract_job_data(url)

    # Crawler should NOT be called
    mock_crawler.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_extract_job_data_empty_crawl_result(service, mock_crawler):
    # Given
    url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123"
    mock_crawler.fetch.return_value = ""  # Empty content

    # When & Then
    with pytest.raises(ValueError, match="Crawled content is empty"):
        await service.extract_job_data(url)


@pytest.mark.asyncio
async def test_extract_job_data_extraction_failure(
    service, mock_crawler, mock_extractor
):
    # Given
    url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123"
    mock_crawler.fetch.return_value = "Content " * 10  # Enough length
    mock_extractor.extract = AsyncMock(return_value=None)  # Extraction Failed

    # When & Then
    with pytest.raises(RuntimeError, match="LLM Extraction returned empty result"):
        await service.extract_job_data(url)
