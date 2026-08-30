import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load the .env file automatically at runtime
load_dotenv()

# 2. Verify the key exists and initialize the Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Error: GEMINI_API_KEY not found in environment or .env file!")

# Initialize the Gemini client
client = genai.Client()

# 3. Define the structure of our input using Pydantic
class TranslationRequest(BaseModel):
    source_payload: dict = Field(..., description="The raw incoming webhook JSON data.")
    target_schema: dict = Field(..., description="The JSON schema specifying the required output format.")

def translate_payload(request: TranslationRequest) -> dict:
    """
    Translates a source JSON payload into a target JSON format 
    specified by a target JSON schema using Google Gemini.
    """
    
    # A. System Prompt: Defining the LLM's Persona and Rules
    system_instruction = (
        "You are a deterministic backend API translator. Your job is to read an incoming "
        "JSON payload and map its fields to match a required target JSON schema. "
        "Perform status mapping (e.g. convert states/strings where necessary), format dates "
        "consistently, and strictly follow the target schema. "
        "Do not include any chat formatting, conversational text, or markdown code blocks. "
        "Output ONLY the raw translated JSON."
    )
    
    # B. User Prompt: Feeding the actual data to map
    user_content = (
        f"Source Payload (Input Data):\n{json.dumps(request.source_payload, indent=2)}\n\n"
        f"Target Schema (Required Output Format):\n{json.dumps(request.target_schema, indent=2)}"
    )
    
    # C. Call the Gemini API with schema enforcement
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            # We tell Gemini to return JSON, matching the requested target schema
            response_mime_type="application/json",
            response_schema=request.target_schema
        ),
    )
    
    # D. Parse the text response back into a Python dictionary
    try:
        translated_data = json.loads(response.text)
        return translated_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON. Response text: {response.text}") from e


# 4. Local Test Block (Only runs when executing this file directly)
if __name__ == "__main__":
    # A. Simulated input data from a source (e.g., checkout system like Shopify)
    sample_source = {
        "id": "ord_998811",
        "customer": {
            "first_name": "Rittvik",
            "last_name": "Vashishtha",
            "email_address": "rittvik@example.com"
        },
        "payment_status": "authorized",
        "created_at": "2026-08-30T10:45:00Z"
    }

    # B. The target schema our CRM/Internal Database expects (Standard JSON Schema format)
    sample_target_schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "buyer_name": {"type": "string"},
            "buyer_email": {"type": "string"},
            "is_paid": {"type": "boolean"},
            "date_formatted": {"type": "string"}
        },
        "required": ["order_id", "buyer_name", "buyer_email", "is_paid", "date_formatted"]
    }

    print("Sending request to Gemini for payload mapping...")
    
    # Create the Pydantic request object
    test_request = TranslationRequest(
        source_payload=sample_source,
        target_schema=sample_target_schema
    )
    
    # Run the translation
    result = translate_payload(test_request)
    
    print("\n--- Translation Results ---")
    print(json.dumps(result, indent=2))
    print("---------------------------")
