import os
from dotenv import load_dotenv

# Load environment variables from a .env file into the environment
load_dotenv()

# Google API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
GEMINI_API = os.getenv('GOOGLE_API_KEY')
IMAGE_ENGINE_ID = os.getenv('IMAGE_ENGINE_ID')

# Firebase configuration
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')

# File storage configuration (for local development)
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')

# Allowed file extensions for uploads
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'm4a'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}

# Timeout setting in seconds (default 30)
timeout = int(os.getenv('DERMAAI_TIMEOUT', '30'))

# Application, API, and LLM model settings
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.0-flash-001')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0'))
LLM_MAX_TOKENS = os.getenv('LLM_MAX_TOKENS')
