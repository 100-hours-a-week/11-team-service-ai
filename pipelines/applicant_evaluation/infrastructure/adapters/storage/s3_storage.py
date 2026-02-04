import asyncio
import boto3
from botocore.exceptions import ClientError
from shared.config import settings
from ....domain.interface.adapter_interfaces import FileStorage


class S3FileStorage(FileStorage):
    """
    AWS S3를 사용하는 파일 스토리지 어댑터 (Async)
    Since boto3 is synchronous, we wrap blocking calls with asyncio.to_thread.
    """

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.AWS_S3_BUCKET_NAME

    async def download_file(self, file_path: str) -> bytes:
        """
        S3에서 파일(Object)을 다운로드하여 바이트로 반환 (Async)
        file_path: S3 Object Key (예: 'resumes/123/resume.pdf')
        """

        def _download_sync():
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            return response["Body"].read()

        try:
            return await asyncio.to_thread(_download_sync)
        except ClientError as e:
            # TODO: 로깅 (e.g. logger.error)
            print(f"S3 Download Error: {e}")
            raise FileNotFoundError(f"Failed to download file from S3: {file_path}")

    async def upload_file(
        self,
        file_content: bytes,
        destination_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        """
        파일을 S3에 업로드하고 Key(Path)를 반환 (Async)
        """

        def _upload_sync():
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=destination_path,
                Body=file_content,
                ContentType=content_type,
            )

        try:
            await asyncio.to_thread(_upload_sync)
            return destination_path
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            raise RuntimeError(f"Failed to upload file to S3: {e}")
