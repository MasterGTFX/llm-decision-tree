"""Configuration parameters for LLM Decision Tree Generator."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Configuration
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.1")

# Tree Building Parameters
MAX_DEPTH = 10  # Maximum tree depth to prevent infinite recursion