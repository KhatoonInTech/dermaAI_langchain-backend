from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Body, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from Agents.input_agent import InputAgent
from Agents.diagnosis_agent import DiagnosisAgent
from Agents.report_generator_agent import ReportGeneratorAgent
from Agents.search_agent import SearchAgent
from Agents.chatbot import ChatbotAgent
from Agents.llms_manager_agent import LLMManager
from Agents.ReportingAnalysisAgent import ReportingAnalysisAgent
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS
import os
import io
import time
# import uuid
import mimetypes
from typing import Optional, Dict, Any, List
from PydanticModels import QuestionRequest, QuestionResponse, AssessmentResponse, ReportAnalysisResponse, ConversationRequest, ConversationResponse, PdfRequest, ArticleSummary, SearchResponse
app = FastAPI(title="DermaAI API",
    description="Simulated dermatology assistant with assessment, report analysis, and conversation capabilities.",
    version="1.1.0",
)

#Creating Instances of the Agentic Classes
Diagnosis_Agent = DiagnosisAgent()
Report_Generator_Agent = ReportGeneratorAgent()
Search_Agent = SearchAgent()
Chatbot_Agent = ChatbotAgent()   
Reporting_Analysis_Agent = ReportingAnalysisAgent()
Input_Agent = InputAgent()


# --- API Endpoints ---

@app.get("/", tags=["General"])
async def read_root():
        """ Root endpoint providing basic API information. """
        return {
            "message": "Welcome to the DermaAI API.",
            "version": app.version,
            "endpoints": {
            "/docs": "This API documentation.",
            "/generate_questions": "POST: Generate follow-up questions based on initial statement/symptoms.",
            "/assess": "POST: Perform a full assessment based on initial text or image/audio.",
            "/analyze_report": "POST: Analyze text from an uploaded PDF/DOCX/Image report.",
            "/continue_conversation": "POST: Continue an existing conversation using a session ID.",
            "/generate_report_pdf": "POST: Generate a PDF report from assessment results.",
            "/search_articles": "POST: Search for articles related to a query and return summaries."
            }
        }
    
@app.post("/search_articles", response_model=SearchResponse, tags=["Research"])
async def search_articles_endpoint(query: str = Body(..., embed=True)):
    """
    Searches for articles related to the query, processes them, and returns summaries.
    """
    print(f"\n--- Article Search Request for: {query} ---")
    start_time = time.time()

    try:
        # Search for articles
        print("Performing Google search...")
        search_results = Search_Agent.search_articles(query, max_results=10)
        if not search_results:
            raise HTTPException(status_code=500, detail="Failed to retrieve search results")

        # Get metadata for all results
        items_count = len(search_results.get('items', []))
        print(f"Processing {items_count} search results...")
        search_metadata = Search_Agent.articles_url(search_results, max_urls=items_count)

        # Process each article
        articles = []
        for article_metadata in search_metadata:
            try:
                Title = article_metadata.get('title', 'No Title')
                print(f"Processing article: {Title[:50]}...")
                
                summary = Search_Agent.summarize_article(article_metadata, query)
                
                articles.append(ArticleSummary(
                    title=Title,
                    snippet=article_metadata.get('snippet', Title),
                    url=article_metadata.get('url', 'No URL'),
                    image=article_metadata.get('image_context'),
                    summary=str(summary)
                ))
            except Exception as article_error:
                print(f"⚠️ Error processing article {Title}: {article_error}")
                continue

        processing_time = round(time.time() - start_time, 2)
        
        if not articles:
            raise HTTPException(status_code=404, detail="No articles could be processed successfully")

        print(f"✅ Successfully processed {len(articles)} articles in {processing_time}s")
        return SearchResponse(
            message="Articles retrieved and processed successfully",
            processing_time_seconds=processing_time,
            query=query,
            articles=articles
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"🚨 Error during article search and processing: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing search request: {str(e)}")

@app.post("/generate_questions", response_model=QuestionResponse, tags=["Assessment Steps"])
async def get_diagnostic_questions_endpoint(request: QuestionRequest = Body(...)):
    """
    Generates potential diagnostic questions based on an initial statement and optional symptoms.
    """
    print("\n--- Generate Questions Request ---")
    start_time = time.time()

    print("Extracting symptoms from statement...")
    symptoms_to_use = Diagnosis_Agent.extract_symptoms(request.statement)
    if not symptoms_to_use: symptoms_to_use = [] # Ensure list

    print(f"Generating questions for statement: \"{request.statement[:100]}...\" with symptoms: {symptoms_to_use}")
    questions = Diagnosis_Agent.generate_diagnosis_questions( symptoms_to_use, request.statement)
    processing_time = round(time.time() - start_time, 2)

    if questions:
        print(f"✅ Questions generated successfully in {processing_time}s.")
        return QuestionResponse(
            message="Diagnostic questions generated successfully.",
            processing_time_seconds=processing_time,
            questions=questions,
            statement_processed=request.statement,
            symptoms_used=symptoms_to_use
        )
    else:
        print(f"❌ Failed to generate questions in {processing_time}s.")
        raise HTTPException(status_code=500, detail="Failed to generate diagnostic questions from the LLM.")


@app.post("/assess", response_model=AssessmentResponse, tags=["Assessment Steps"])
async def create_assessment_endpoint(
    background_tasks: BackgroundTasks,
    text_input: Optional[str] = Form(None),
    file_input: Optional[UploadFile] = File(None)
):
    """
    Performs a full simulated assessment based on initial text, image, or audio input.
    """
    print("\n--- Full Assessment Request ---")
    start_time = time.time()
    if not text_input and not file_input:
        raise HTTPException(status_code=400, detail="Provide either 'text_input' or 'file_input'.")
    if text_input and file_input:
        raise HTTPException(status_code=400, detail="Provide only one of 'text_input' or 'file_input'.")

    try:
        initial_statement, visual_description, _, _ = await Input_Agent.process_input(text_input, file_input)
    except HTTPException as e:
        raise e
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error processing input: {e}")


    try:
        print("Extracting symptoms...")
        symptoms = Diagnosis_Agent.extract_symptoms( initial_statement)

        print("Getting initial diagnosis...")
        init_diagnosis = Diagnosis_Agent.get_initial_diagnosis()
        if not init_diagnosis: raise HTTPException(status_code=500, detail="Failed to get initial analysis from LLM.")

        print("Performing deep research...")
        research_texts = Diagnosis_Agent.deep_diagnosis_research(init_diagnosis)

        print("Getting final assessment...")
        final_assessment = Diagnosis_Agent.get_final_diagnosis(research_texts)
        if not final_assessment: raise HTTPException(status_code=500, detail="Failed to get final assessment from LLM.")

        print("Generating report markdown...")
        report_markdown = Report_Generator_Agent.generate_report_markdown(final_assessment)

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        print(f"--- Assessment Complete (Duration: {processing_time}s) ---")

        return AssessmentResponse(
            message="Assessment completed successfully.",
            processing_time_seconds=processing_time,
            final_assessment=final_assessment,
            report_markdown=report_markdown,
            initial_diagnosis=init_diagnosis,
            extracted_symptoms=symptoms,
            visual_description_if_any=visual_description,
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"🚨 Unexpected Error during assessment processing: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error during assessment: {e}")


@app.post("/analyze_report", response_model=ReportAnalysisResponse, tags=["Utilities"])
async def analyze_report_endpoint(report_file: UploadFile = File(...)):
    """
    Analyzes an uploaded report file (PDF, DOCX, Image) using OCR/text extraction
    and asks the LLM to summarize it in simple terms.
    """
    print("\n--- Analyze Report Request ---")
    start_time = time.time()

    max_size = 20 * 1024 * 1024
    size = await report_file.read()
    await report_file.seek(0)
    if len(size) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {max_size // 1024 // 1024}MB.")

    file_bytes = await report_file.read()
    filename = report_file.filename
    mime_type = report_file.content_type
    if not mime_type or mime_type == 'application/octet-stream':
        mime_type, _ = mimetypes.guess_type(filename)
    await report_file.close()

    if not mime_type:
         raise HTTPException(status_code=415, detail="Could not determine file MIME type.")
    print(f"Analyzing file: {filename}, Type: {mime_type}")

    analysis_result = Reporting_Analysis_Agent.analyze_report_file(file_bytes, mime_type)
    processing_time = round(time.time() - start_time, 2)

    if analysis_result.startswith("Error:"):
        print(f"❌ Report analysis failed in {processing_time}s: {analysis_result}")
        status_code = 500 if "LLM" in analysis_result or "unexpected" in analysis_result else 400
        raise HTTPException(status_code=status_code, detail=analysis_result)
    else:
        print(f"✅ Report analysis successful in {processing_time}s.")
        return ReportAnalysisResponse(
            message="Report analyzed successfully.",
            processing_time_seconds=processing_time,
            analysis_summary=analysis_result,
            file_processed=filename,
            mime_type=mime_type
        )

@app.post("/generate_report_pdf", tags=["Reporting"])
async def create_report_pdf_endpoint(request: PdfRequest = Body(...)):
    """
    Generates a downloadable PDF report from assessment results.
    """
    print("\n--- PDF Generation Request ---")
    start_time = time.time()
    report_markdown = request.report_markdown

    try:
        if not report_markdown:
            print("Generating markdown for PDF...")
            report_markdown = Report_Generator_Agent.generate_report_markdown(request.final_assessment, request.visual_description)
            if report_markdown.startswith("Error:"):
                raise HTTPException(status_code=500, detail=f"Failed to generate report content: {report_markdown}")

        print("Generating PDF from markdown...")
        pdf_bytes = Report_Generator_Agent.markdown_to_pdf(report_markdown)
        processing_time = round(time.time() - start_time, 2)

        if pdf_bytes:
            print(f"✅ PDF generated successfully in {processing_time}s.")
            filename = f"Simulated_Dermatology_Report_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            print(f"❌ PDF generation failed in {processing_time}s (likely WeasyPrint issue).")
            raise HTTPException(status_code=500, detail="Failed to generate PDF report. Check server logs and WeasyPrint dependencies.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"🚨 Unexpected Error during PDF generation: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error during PDF generation: {e}")


@app.post("/continue_conversation", response_model=ConversationResponse, tags=["Conversation"])
async def continue_conversation_endpoint(request: ConversationRequest = Body(...)):
    """
    Continues an existing conversation or starts a new one.
    Uses simple in-memory storage (NOT FOR PRODUCTION).
    """
    print("\n--- Continue Conversation Request ---")
    start_time = time.time()
    # session_id = request.session_id
    user_query = request.query

    # if session_id and session_id in conversation_histories:
    #     print(f"Continuing session: {session_id}")
    #     chat_session = conversation_histories[session_id]
    #     if not isinstance(chat_session, ChatSession):
    #          print(f"⚠️ Invalid object found in history for session {session_id}. Starting new session.")
    #          session_id = str(uuid.uuid4())
    #          chat_session = model.start_chat(history=[])
    # else:
    #     session_id = str(uuid.uuid4()) # Generate new ID
    #     print(f"Starting new session: {session_id}")
    #     chat_session = model.start_chat(history=[]) # Initialize a new ChatSession

    # --- Call the new function from Agents/chatbot.py ---
    llm_response = Chatbot_Agent.generate_chat_response(user_query)

    
    processing_time = round(time.time() - start_time, 2)

    if llm_response.startswith("Error:"):
        print(f"❌ LLM error during conversation in {processing_time}s: {llm_response}")
        # Return error response but include session_id
        return ConversationResponse(
            # session_id=session_id,
            response=llm_response,
            processing_time_seconds=processing_time
        )
    else:
        print(f"✅ Conversation response generated successfully in {processing_time}s.")
        return ConversationResponse(
            # session_id=session_id,
            response=llm_response,
            processing_time_seconds=processing_time
        )



# --- Run Instruction (for local development) ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True, workers=1)
    
