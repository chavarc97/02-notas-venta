import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime


class S3Service:
    def __init__(self):
        # If credentials are provided, use them; otherwise let boto3 use the EC2 instance role
        kwargs = {"region_name": os.getenv("AWS_REGION", "us-east-1")}
        if os.getenv("AWS_ACCESS_KEY_ID"):
            kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
            kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
            kwargs["aws_session_token"] = os.getenv("AWS_SESSION_TOKEN")
        self.s3_client = boto3.client("s3", **kwargs)
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")

    def upload_pdf(self, pdf_bytes, key_name):
        try:
            metadata = {
                "hora-envio": str(
                    datetime.now().timestamp()
                ),  # We'll just define an initial timestamp
                "nota-descargada": "false",
                "veces-enviado": "1",
            }

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key_name,
                Body=pdf_bytes,
                ContentType="application/pdf",
                Metadata=metadata,
            )
            return True, None
        except ClientError as e:
            return False, str(e)

    def get_pdf(self, key_name):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key_name)
            return response["Body"].read(), response.get("Metadata", {})
        except ClientError as e:
            return None, str(e)

    def set_nota_descargada(self, key_name):
        # S3 objects are immutable, so to update metadata we copy it over itself
        try:
            # First, fetch existing metadata to keep other values
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key_name)
            metadata = response.get("Metadata", {})

            # Update only the flag
            metadata["nota-descargada"] = "true"

            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                Key=key_name,
                CopySource={"Bucket": self.bucket_name, "Key": key_name},
                Metadata=metadata,
                MetadataDirective="REPLACE",
            )
            return True
        except ClientError:
            return False

    def increment_enviado(self, key_name):
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key_name)
            metadata = response.get("Metadata", {})

            current_count = int(metadata.get("veces-enviado", "0"))

            metadata["veces-enviado"] = str(current_count + 1)
            metadata["hora-envio"] = str(datetime.now().timestamp())

            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                Key=key_name,
                CopySource={"Bucket": self.bucket_name, "Key": key_name},
                Metadata=metadata,
                MetadataDirective="REPLACE",
            )
            return True
        except ClientError:
            return False
