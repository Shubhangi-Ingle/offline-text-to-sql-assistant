import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
READONLY_DB_USER = os.getenv("READONLY_DB_USER")
READONLY_DB_PASSWORD = os.getenv("READONLY_DB_PASSWORD")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")

USE_LLM_TRIAGE = os.getenv("USE_LLM_TRIAGE", "true").lower() == "true"