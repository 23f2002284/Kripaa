import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/kripaa_db")
    
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Paths
    DATA_DIR = os.getenv("DATA_DIR", "data")
    PDF_DIR = os.path.join(DATA_DIR, "pdfs")
    
    # Model Settings
    DEFAULT_MODEL = "gpt-4o" # or "gemini-1.5-pro"
