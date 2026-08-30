from fastapi import FastAPI, HTTPException, status
from translator import TranslationRequest, translate_payload

app = FastAPI(
    title="Smart Webhook Adapter Gateway",
    description="A secure, LLM-powered API integration adapter that translates schemas on the fly.",
    version="1.0.0"
)

# 1. Prompt Injection Detection Helper
def contains_prompt_injection(data: dict) -> bool:
    """
    Recursively scans the dictionary values for common prompt injection patterns.
    """
    # A list of typical injection trigger phrases
    suspicious_patterns = [
        "ignore previous",
        "ignore all",
        "override system",
        "system instruction",
        "new rule",
        "forget your"
    ]
    
    for key, value in data.items():
        if isinstance(value, dict):
            # If nested dictionary, recurse
            if contains_prompt_injection(value):
                return True
        elif isinstance(value, str):
            # Clean and lowercase the input text for matching
            val_lower = value.lower()
            
            # Attack Defense A: Max length check for any text field
            if len(val_lower) > 2000:
                return True
                
            # Attack Defense B: Keyword scanning
            for pattern in suspicious_patterns:
                if pattern in val_lower:
                    return True
    return False

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "webhook-translator"}

@app.post("/translate")
def translate_webhook(payload: TranslationRequest):
    # 2. Run the security filter before sending to Gemini
    if contains_prompt_injection(payload.source_payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Alert: Malicious input or potential prompt injection detected."
        )
        
    try:
        translated_result = translate_payload(payload)
        return {"success": True, "data": translated_result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal translation error: {str(e)}"
        )
