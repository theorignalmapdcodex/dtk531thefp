import google.generativeai as genai
from typing import List, Optional

# # Function to query Gemini API (Text)
# Conversation history (list of dictionaries)
conversation_history = []

def query_gemini_api(user_text: str, gemini_model: genai.GenerativeModel, history: list) -> str:
    """Queries the Gemini API, including conversation history."""
    try:
        prompt = user_text  # Start with the user's text

        # Adding conversation history to the prompt (if any); Modified with Gemini AI on 4 Feb 25 @ 1:35pm
        if history:
            formatted_history = ""
            for turn in history:
                formatted_history += f"User: {turn['user']}\nGemini: {turn['gemini']}\n"

            prompt = formatted_history + prompt  # Prepend history to current prompt

        response = gemini_model.generate_content(prompt)
        response.resolve()
        gemini_response = response.text

        # Update conversation history
        history.append({"user": user_text, "gemini": gemini_response})

        return gemini_response

    except Exception as e:
        return f"An error occurred: {e}"