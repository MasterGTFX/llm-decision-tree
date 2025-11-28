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

# Predefined Roles
PREDEFINED_ROLES = [
    {
        "id": "medical",
        "name": "Medical Diagnosis Expert",
        "emoji": "🩺",
        "default_query": "I have a headache and fever."
    },
    {
        "id": "relationship",
        "name": "Relationship Advisor",
        "emoji": "❤️",
        "default_query": "My partner and I are arguing about finances."
    },
    {
        "id": "career",
        "name": "Career Counselor",
        "emoji": "💼",
        "default_query": "I'm feeling stuck in my current job and want a change."
    },
    {
        "id": "tech",
        "name": "Technical Troubleshooter",
        "emoji": "💻",
        "default_query": "My computer screen keeps flickering."
    },
    {
        "id": "fitness",
        "name": "Fitness Coach",
        "emoji": "💪",
        "default_query": "I want to start a weight loss journey."
    }
]