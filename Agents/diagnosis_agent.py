import re
import json
from Agents.llms_manager_agent import LLMManager
from Agents.search_agent import SearchAgent

class DiagnosisAgent:
    def __init__(self):
      self.llm = LLMManager()
      self.search= SearchAgent()

    def extract_symptoms(self, statement):
        """Extracts symptoms from the user statement using the LLM."""
        prompt = f"""
        Patient statement: "{statement}"

        Review the patient statement above. Extract all the key **symptoms** mentioned (e.g., REDNESS, ITCHING, RASH, PAIN, BLISTERS, LESION, SCALY PATCH). Be specific.
        Return ONLY a JSON array of uppercase strings (e.g., ["RASH", "ITCHING","PAIN","BLISTERS"]). If no clear symptoms are mentioned, return an empty array [].
        Do not include explanations or any text outside the JSON array.
        """
        symptoms = self.llm.send_message_to_llm(prompt)
        return symptoms

    def generate_diagnosis_questions(self, symptoms, statement):
        """
        Generates follow-up questions based on extracted symptoms and statement using the LLM.
        Does NOT handle user input; returns the list of questions.

        Args:
            chat_session: The active chat session with the LLM.
            symptoms: A list of extracted symptoms.
            statement: The initial user statement or context.

        Returns:
            A list of question strings if successful, otherwise None.
        """
        if not symptoms:
            print("No specific symptoms identified to base questions on. Asking general questions.")
            symptoms_str = "a general skin concern" # Slightly better phrasing for prompt
        else:
            symptoms_str = ", ".join(symptoms)

        prompt = f"""
        Based on the patient mentioning symptoms like: {symptoms_str} and the initial statement: "{statement}".

        Generate **exactly 5** concise follow-up questions a dermatologist might ask to clarify the condition.
        Focus on clarifying: Severity, Duration, Triggers, Location/Spread, Associated factors (fever, etc.), Previous treatments/attempts.
        Phrase the questions clearly and directly as if asking a patient.
        Return ONLY a **strict JSON array** containing exactly 5 strings (the questions). Do not include numbering, introductions, or any other text outside the JSON array.
        Example Format: ["How long have you had these symptoms?", "On a scale of 1-10, how severe is the itching?", ...]
        """
        questionaire = self.llm.send_message_to_llm(prompt)
        return questionaire

    def get_initial_diagnosis(self):
        prompt = (
            "Using the chat history (patient statement, symptoms, follow-ups), perform an **initial dermatological analysis**. "
            "Return a **strict JSON object** with these keys:\n"
            "  • \"most_likely_diagnosis\": string\n"
            "  • \"justification\": string (reference visual features)\n"
            "  • \"diseases\": {\"Disease1\": %, \"Disease2\": %, \"Disease3\": %}\n"
            "  • \"differential_diagnosis\": {\"Alt1\": \"reason\", \"Alt2\": \"reason\", \"Alt3\": \"reason\"}\n"
            "Do not include any extra keys or prose."
        )
        init_diag = self.llm.send_message_to_llm(prompt)
        return init_diag

    def deep_diagnosis_research(self, pre_diag_dict):
        disease_search = []
        for disease in pre_diag_dict.keys():
            deep_search = self.search.deepsearch(disease)
            disease_search.extend(deep_search)
        return disease_search

    def get_final_diagnosis(self, deep_research):
        joined_research = " ".join(deep_research)
        prompt = (
            f"Considering the deep research texts {joined_research} and prior chat history, select the **one** best final diagnosis. "
            "Return a **strict JSON** with:\n"
            "  • \"disease\": string\n"
            "  • \"justification\": string\n"
            "  • \"possible_causes\": string\n"
            "  • \"differential_diagnosis\": {\n"
            "      \"Alt1\": {\"disease\":string, \"justification_and_causes\":string},\n"
            "      \"Alt2\": {…}\n"
            "    }\n"
            "  • \"treatment_and_recommendation\": string\n"
            "  • \"conclusion\": string\n"
            "No extra commentary—only this JSON."
        )
        final_diag = self.llm.send_message_to_llm(prompt)
        return final_diag
