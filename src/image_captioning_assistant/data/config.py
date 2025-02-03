import os

from image_captioning_assistant.aws.get_secret import get_secret


DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']

# Check if we're in development or production
if os.environ.get('ENVIRONMENT') == 'production':
    # In production, these will be set as environment variables
    DB_USER = os.environ['DB_USER']
    DB_PASSWORD = os.environ['DB_PASSWORD']
else:
    # In development, fetch from Secrets Manager
    DB_SECRET_NAME = os.environ['DB_SECRET_NAME']
    AWS_REGION = os.environ['AWS_REGION']
    credentials = get_secret(secret_name=DB_SECRET_NAME, region_name=AWS_REGION)
    DB_USER = credentials['username']
    DB_PASSWORD = credentials['password']

# Database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"