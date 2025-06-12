import os
from fastapi import  File, UploadFile, HTTPException
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS, UPLOAD_FOLDER
import mimetypes
from typing import Optional
from Agents.llms_manager_agent import LLMManager
class InputAgent:

    def __init__(self):
        self.llm = LLMManager()  # Initialize the LLM manager

    @staticmethod
    def allowed_file(filename, allowed_exts):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

   
    @staticmethod
    def validate_image_extension(filename):
        if not InputAgent.allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            raise ValueError("Invalid image file extension.")
        return True

    @staticmethod
    def validate_audio_extension(filename):
        if not InputAgent.allowed_file(filename, ALLOWED_AUDIO_EXTENSIONS):
            raise ValueError("Invalid audio file extension.")
        return True
    
    # --- Helper Function for Input Processing ---
    # ... (process_input remains the same) ...
    async def process_input(self, text_input: Optional[str], file_input: Optional[UploadFile]) -> tuple[str, Optional[str], Optional[bytes], Optional[str]]:
        """Processes text or file input, returning initial statement, visual description, content, mime type."""
        initial_statement = ""
        visual_description = None
        file_content = None
        mime_type = None

        if file_input:
            file_content = await file_input.read()
            mime_type = file_input.content_type
            if not mime_type or mime_type == 'application/octet-stream':
                mime_type, _ = mimetypes.guess_type(file_input.filename)
                print(f"Guessed MIME type as: {mime_type} for file {file_input.filename}")

            if not mime_type:
                await file_input.close()
                raise HTTPException(status_code=415, detail=f"Could not determine MIME type for file: {file_input.filename}")

            print(f"Processing uploaded file: {file_input.filename}, Type: {mime_type}")

            if mime_type in ALLOWED_IMAGE_EXTENSIONS:
                print("Input is an image. Generating visual description...")
                visual_description = self.llm.describe_visuals(file_content, mime_type)
                if isinstance(visual_description, str) and visual_description.startswith("Error:"):
                    await file_input.close()
                    raise HTTPException(status_code=500, detail=f"Failed to analyze image: {visual_description}")

                summary_prompt = f"Based on the following detailed visual description of a skin condition, create a concise one-sentence summary statement suitable as an initial patient complaint:\n\n{visual_description}"
                initial_statement_raw = self.llm.send_message_to_llm( summary_prompt)
                if isinstance(initial_statement_raw, str) and not initial_statement_raw.startswith("Error:"):
                    initial_statement = f"Image analysis summary: {initial_statement_raw.strip()}"
                else:
                    print("⚠️ Could not generate summary from visual description, using description directly.")
                    initial_statement = f"Visual Description from Image:\n{visual_description}"

            
            else:
                await file_input.close()
                raise HTTPException(status_code=415, detail=f"Unsupported file type for initial assessment intake: {mime_type}. Use /analyze_report for PDF/DOCX/Image analysis.")

            await file_input.close()

        elif text_input:
            initial_statement = text_input.strip()
            if not initial_statement:
                raise HTTPException(status_code=400, detail="Text input cannot be empty.")
            print(f"Input is text: \"{initial_statement[:100]}...\"")

        if not initial_statement:
            raise HTTPException(status_code=500, detail="Failed to establish an initial statement from input.")

        return initial_statement, visual_description, file_content, mime_type


