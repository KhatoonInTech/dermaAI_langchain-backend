from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# --- Pydantic Models ---
class QuestionRequest(BaseModel):
    statement: str = Field(..., description="Initial user statement about their concern.", example="I have an itchy red rash on my arm.")
    # symptoms: Optional[List[str]] = Field(None, description="Optional pre-extracted list of symptoms.", example=["RASH", "ITCHING", "REDNESS"])

class QuestionResponse(BaseModel):
    message: str
    processing_time_seconds: float
    questions: List[str]
    statement_processed: str
    symptoms_used: List[str]

class AssessmentResponse(BaseModel):
    message: str
    processing_time_seconds: float
    final_assessment: Dict[str, Any]
    report_markdown: str
    initial_diagnosis: Optional[Dict[str, Any]] = None
    extracted_symptoms: Optional[List[str]] = None
    visual_description_if_any: Optional[str] = None

class ReportAnalysisResponse(BaseModel):
    message: str
    processing_time_seconds: float
    analysis_summary: str
    file_processed: str
    mime_type: str

class ConversationRequest(BaseModel):
    # session_id: Optional[str] = Field(None, description="Existing session ID to continue a conversation. If None, a new session starts.")
    query: str = Field(..., description="The user's latest message or question.")

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    processing_time_seconds: float

class PdfRequest(BaseModel):
    final_assessment: Dict[str, Any] = Field(..., description="The final_assessment object from the /assess endpoint.")
    visual_description: Optional[str] = Field(None, description="Optional visual description if an image was processed.")
    report_markdown: Optional[str] = Field(None, description="Optional pre-generated markdown report.")

class ArticleSummary(BaseModel):
    title: str
    snippet: str
    url: str
    image: Optional[str] = None
    summary: str

class SearchResponse(BaseModel):
    message: str
    processing_time_seconds: float
    articles: List[ArticleSummary]
    query: str
