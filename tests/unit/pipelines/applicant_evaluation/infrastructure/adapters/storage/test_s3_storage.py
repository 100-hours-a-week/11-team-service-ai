import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from pipelines.applicant_evaluation.infrastructure.adapters.storage.s3_storage import (
    S3FileStorage,
)


@pytest.fixture
def mock_s3_client():
    with patch(
        "pipelines.applicant_evaluation.infrastructure.adapters.storage.s3_storage.boto3.client"
    ) as mock:
        yield mock


@pytest.fixture
def storage(mock_s3_client):
    # 생성자에서 boto3.client 호출됨 -> mock_s3_client가 반환하는 객체가 self.s3_client가 됨
    return S3FileStorage()


@pytest.mark.asyncio
async def test_download_file_success(storage):
    """S3 파일 다운로드 성공 시 바이트 반환"""
    # 1. Setup Mock
    mock_body = MagicMock()
    mock_body.read.return_value = b"PDF_CONTENT"

    # get_object 리턴값: {'Body': mock_body}
    storage.s3_client.get_object.return_value = {"Body": mock_body}

    # 2. Execute
    result = await storage.download_file("test/file.pdf")

    # 3. Verify
    assert result == b"PDF_CONTENT"
    storage.s3_client.get_object.assert_called_once()
    # Bucket 이름 등 인자 검증도 가능
    # call_args = storage.s3_client.get_object.call_args
    # assert call_args.kwargs['Key'] == "test/file.pdf"


@pytest.mark.asyncio
async def test_download_file_not_found(storage):
    """S3 에러 발생 시 FileNotFoundError로 변환하여 발생"""
    # 1. Setup Error
    error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
    storage.s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    # 2. Execute & Verify
    with pytest.raises(FileNotFoundError, match="Failed to download"):
        await storage.download_file("missing.pdf")


@pytest.mark.asyncio
async def test_upload_file_success(storage):
    """S3 업로드 성공 테스트"""
    # 1. Execute
    file_bytes = b"New Content"
    path = "uploads/new.pdf"

    result = await storage.upload_file(file_bytes, path)

    # 2. Verify
    assert result == path
    storage.s3_client.put_object.assert_called_once()

    # Check arguments
    call_kwargs = storage.s3_client.put_object.call_args.kwargs
    assert call_kwargs["Key"] == path
    assert call_kwargs["Body"] == file_bytes
    assert call_kwargs["ContentType"] == "application/pdf"
