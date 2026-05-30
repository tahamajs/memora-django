import boto3
from django.core.files.storage import Storage
from django.conf import settings

class S3Storage(Storage):
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def _save(self, name, content):
        self.client.upload_fileobj(content, self.bucket, name)
        return name

    def _open(self, name, mode='rb'):
        from io import BytesIO
        obj = self.client.get_object(Bucket=self.bucket, Key=name)
        return BytesIO(obj['Body'].read())

    def exists(self, name):
        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except: return False

    def url(self, name):
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': name},
            ExpiresIn=3600
        )

class R2Storage(S3Storage):
    """Cloudflare R2 – identical to S3, just different endpoint."""
    pass

class MinIOStorage(S3Storage):
    pass
