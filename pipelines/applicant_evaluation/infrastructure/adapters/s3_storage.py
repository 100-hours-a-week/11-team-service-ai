import boto3
from botocore.exceptions import ClientError
from ai.shared.config import settings
from ...domain.interface.adapter_interfaces import FileStorage

class S3FileStorage(FileStorage):
    """
    AWS S3를 사용하는 파일 스토리지 어댑터
    """
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_S3_BUCKET_NAME

    def download_file(self, file_path: str) -> bytes:
        """
        S3에서 파일(Object)을 다운로드하여 바이트로 반환
        file_path: S3 Object Key (예: 'resumes/123/resume.pdf')
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=file_path
            )
            return response['Body'].read()
            
        except ClientError as e:
            # TODO: 로깅 (e.g. logger.error)
            print(f"S3 Download Error: {e}")
            raise FileNotFoundError(f"Failed to download file from S3: {file_path}")
