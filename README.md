# DermaAI

DermaAI is a modular dermatology assistant designed to run locally or be deployed on the cloud. It leverages state-of-the-art Large Language Models (LLMs) such as Gemini, integrates Google APIs, supports robust audio and image input, performs web search and scraping, generates professional PDF reports, and manages files via Firebase storage.

---

## Features

- Accepts natural language, audio, or image input for dermatological analysis
- Performs step-by-step clinical reasoning and evidence-based diagnosis
- Provides actionable recommendations based on diagnosis
- Generates detailed PDF reports for clinical use
- Conducts robust web search and content scraping for supplementary data
- Modular, agent-based architecture for easy extension and maintenance
- Comprehensive error handling for reliable operation
- FastAPI backend for scalable agent orchestration and API exposure
- Firebase integration for secure file upload, storage, and retrieval

---

## Project Structure

```
dermaAI/
├── app.py                  # FastAPI application with endpoints for all agents
├── config.py               # Centralized configuration (API keys, environment variables, constants)
├── database.py             # Firebase and database integration utilities
├── requirements.txt        # Python package dependencies
├── README.md               # This documentation
│
└── Agents/
    ├── __init__.py
    ├── diagnosis_agent.py         # Diagnosis logic and clinical workflow orchestration
    ├── input_agent.py             # Handles user audio, image, and text input processing
    ├── llms_manager_agent.py     # Interfaces Gemini LLM via LangChain for reasoning
    ├── report_generator_agent.py # Generates professional PDF reports from markdown
    └── search_agent.py            # Performs web search and scraping with Google Custom Search and BeautifulSoup
```

---

## Getting Started

### 1. Clone the repository and install dependencies

```bash
git clone <repo-url>
cd dermaAI
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the `dermaAI/` root directory with the following content:

```
GOOGLE_API_KEY=your_google_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here
GEMINI_API=your_gemini_api_key_here
IMAGE_ENGINE_ID=your_image_engine_id_here
FIREBASE_CREDENTIALS=path/to/firebase/credentials.json
```

- Replace placeholder values with your actual API keys and credentials.
- The Firebase credentials JSON file can be obtained from your Firebase Console.

### 3. Run the application

```bash
uvicorn dermaAI.app:app --reload
```

- The FastAPI server will start locally at `http://127.0.0.1:8000/`
- Access the interactive API documentation at `http://127.0.0.1:8000/docs`

---

## Agent Overview

DermaAI is composed of modular agents, each responsible for a specific aspect of the dermatology assistant workflow:

- **input_agent.py**
  Handles all user inputs including text, audio (via SpeechRecognition), and image parsing.

- **llms_manager_agent.py**
  Interfaces with the Gemini LLM through LangChain to perform clinical reasoning and generate responses.

- **diagnosis_agent.py**
  Orchestrates the diagnostic workflow, applying step-by-step dermatological logic and evidence synthesis.

- **search_agent.py**
  Utilizes Google Custom Search API and BeautifulSoup to retrieve relevant images and web content for diagnosis support.

- **report_generator_agent.py**
  Converts markdown-based diagnostic summaries into professional PDF reports using WeasyPrint, embedding images and references.

---

## API Endpoints

The FastAPI backend exposes the following key endpoints for interaction:

| Endpoint      | Method | Description                                  |
|---------------|--------|----------------------------------------------|
| `/input/`     | POST   | Submit user input (text, audio, or image)   |
| `/diagnose/`  | POST   | Trigger the core diagnostic workflow         |
| `/report/`    | GET/POST | Generate and retrieve PDF diagnostic report |
| `/search/`    | GET    | Perform web search for images and articles   |
| `/upload/`    | POST/GET | Upload and download files via Firebase       |

- Detailed OpenAPI documentation is available at `/docs` after launching the server.

---

## Important: Google & Gemini API Setup

- **Google Cloud Custom Search**
  Set up a Custom Search Engine and obtain your API key and Search Engine ID.
  Documentation: https://developers.google.com/custom-search/v1/overview

- **Gemini LLM (via LangChain)**
  Obtain your Gemini API key and configure LangChain integration accordingly.

- **Firebase**
  Create a Firebase project and download the service account credentials JSON file.
  Set the `FIREBASE_CREDENTIALS` environment variable to the path of this file.

---

## System Requirements

- Python 3.8 or higher
- Compatible with Linux, macOS, and Windows
- pip and virtual environment support (`venv`)

---

## Author & License

Developed by yourname.
Licensed under the MIT License. Contributions and feature requests are welcome.

---

Thank you for using DermaAI — your intelligent dermatology assistant.
