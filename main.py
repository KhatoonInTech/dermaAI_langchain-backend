from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from Agents.input_agent import InputAgent
from Agents.llms_manager_agent import LLMManager
from Agents.diagnosis_agent import DiagnosisAgent
from Agents.report_generator_agent import ReportGeneratorAgent
from Agents.search_agent import SearchAgent
import config
import os

app = FastAPI(title="DermaAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint that provides API information"""
    return {
        "name": "DermaAI API",
        "version": "1.0.0",
        "description": "A dermatology assistant API using AI for diagnosis and reporting",
        "endpoints": {
            "POST /input/text/": "Submit text description of symptoms",
            "POST /input/audio/": "Submit audio recording of symptoms",
            "POST /input/image/": "Submit image of affected area",
            "POST /diagnose/": "Get AI diagnosis based on inputs",
            "POST /report/": "Generate PDF report from diagnosis",
            "GET /search/": "Search for related medical information",
            "POST /upload/": "Upload files to storage",
            "GET /download/": "Download files from storage"
        }
    }

@app.post("/input/text/")
def text_input(statement: str = Form(...)):
    return {"text": statement}

@app.post("/input/audio/")
def audio_input(file: UploadFile = File(...)):
    filename = file.filename
    InputAgent.validate_audio_extension(filename)
    temp_path = os.path.join(config.UPLOAD_FOLDER, filename)
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
    try:
        transcription = InputAgent.transcribe_audio(temp_path)
    finally:
        os.remove(temp_path)
    return {"transcription": transcription}

@app.post("/input/image/")
def image_input(file: UploadFile = File(...)):
    filename = file.filename
    InputAgent.validate_image_extension(filename)
    temp_path = os.path.join(config.UPLOAD_FOLDER, filename)
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
    return {"image_path": temp_path}

@app.post("/diagnose/")
def diagnose(statement: str = Form(...)):
    agent = DiagnosisAgent()
    try:
        symptoms = agent.user_symptoms(statement)
        questions = agent.diagnosis_questionnaire(symptoms)
        # questions would be surfaced to the user for answers;
        # for demo: skip user follow-up answers, or accept via API
        initial_diag = agent.initial_diagnosis()
        research = agent.deep_diagnosis_research(initial_diag)
        final_diag = agent.final_diagnosis(research)
        return {"final_diagnosis": final_diag}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/report/")
def report_endpoint(final_diagnose: dict):
    try:
        report_md = ReportGeneratorAgent.generate_report_markdown(final_diagnose)
        pdf_path = ReportGeneratorAgent.markdown_to_pdf(report_md, filename="output_dermaai_report.pdf")
        return FileResponse(pdf_path, media_type="application/pdf", filename="derma_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(query: str = None): 
    """
    Search for images and articles related to a dermatological condition.
    
    Args:
        query (str): The skin condition or symptom to search for
    """
    if not query:
        raise HTTPException(
            status_code=422, 
            detail="Query parameter is required. Example: /search?query=acne"
        )
    
    try:
        img_results = SearchAgent.search_images(query)
        imgs = SearchAgent.imgs_url(img_results)
        article_results = SearchAgent.search_articles(query)
        urls = SearchAgent.articles_url(article_results)
        return {
            "query": query,
            "images": imgs, 
            "articles": urls
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
