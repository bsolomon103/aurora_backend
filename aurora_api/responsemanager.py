from .celeryfuncs import cache_chat_message
import torch
import random
import boto3
import os
import time
from django.conf import settings
from .models import Customer
#Booking, Treatment


def download_file_from_s3(local_directory, file_reference):
    s3 = boto3.client('s3')
    bucket_name = os.environ['AWS_STORAGE_BUCKET_NAME']
    directory = os.path.join(settings.BASE_DIR, 'media')  # Local file path where you want to save the downloaded file
    file_path = os.path.join(directory, local_directory, file_reference)
    print(file_path)
    
    try:
        s3.download_file(bucket_name, file_reference, file_path)
        return file_path
    except Exception as e:
        # Handle exceptions (e.g., file not found in S3, permissions issues, etc.)
        print(f"Error: {e}")
        return None

        
def download_s3_folder(s3_folder, local_dir=None):
    """
    Download the contents of a folder directory
    Args:
        bucket_name: the name of the s3 bucket
        s3_folder: the folder path in the s3 bucket
        local_dir: a relative or absolute directory path in the local file system
    """
    s3 = boto3.resource('s3')
    bucket_name = os.environ['AWS_STORAGE_BUCKET_NAME']
    bucket = s3.Bucket(bucket_name)
    # Extract the folder name from the S3 folder path
    folder_name = os.path.basename(s3_folder.rstrip('/'))
    
    for obj in bucket.objects.filter(Prefix=s3_folder):
        print(obj.key)
        target = obj.key if local_dir is None \
            else os.path.join(local_dir, folder_name, os.path.relpath(obj.key, s3_folder))
        
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        if obj.key[-1] == '/':
            continue
        bucket.download_file(obj.key, target)
        

def get_or_download_secret(secret_file):
     # Specify the local file path where you expect the training file to be
    local_file = os.path.join(settings.BASE_DIR, 'media', 'secrets_file', secret_file)

    # Check if the local file exists
    if os.path.exists(local_file):
        return local_file
    else:
        # The local file doesn't exist, download it from S3
        local_trainingfile = download_file_from_s3('secrets_file', secret_file)
        if local_trainingfile:
            return local_file