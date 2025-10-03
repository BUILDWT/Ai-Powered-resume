import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    """
    Configuration class to hold all environment variables and settings.
    """
    # GCP Settings
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_REGION = os.getenv("GCP_REGION", "us-central1")

    # Cloud Storage
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

    # Firestore Settings
    FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "portfolio_documents")

    # Vertex AI / Gemini Settings
    VERTEX_AI_MODEL_NAME = os.getenv("VERTEX_AI_MODEL_NAME", "gemini-1.0-pro")

    # Embedding Model Settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Document Processing Settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

    # API Security
    API_KEY = os.getenv("API_KEY")

# Instantiate the config
config = Config()

# Basic validation
if not all([config.GCP_PROJECT_ID, config.GCS_BUCKET_NAME, config.API_KEY]):
    raise ValueError("Missing required environment variables: GCP_PROJECT_ID, GCS_BUCKET_NAME, API_KEY")
