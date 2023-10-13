from django.db import models
import os
import boto3

class S3FileField(models.FileField):
    def generate_filename(self, instance, filename):
        #Use customer name to create filename
        ext = os.path.splitext(filename)[1]
        filename = f"{instance.customer_name}{ext}"
        return filename

    def upload_to(self, instance, filename):
        return f"os.environ['AWS_STORAGE_BUCKET_NAME']/{self.generate_filename(instance, filename)}"

    def get_s3_url(self, instance, filename):
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ['AWS_STORAGE_BUCKET_NAME'], 'Key': filename},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return url