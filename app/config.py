import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DB_URL = os.getenv("POSTGRES_DB_URL")
QDRANT_URL = os.getenv("QDRANT_URL", "https://aff5a553-d08d-4b6f-a735-a9bbabf90785.eu-central-1-0.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
UPLOAD_DIR = "sample_kb/kb"
