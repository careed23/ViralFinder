import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# Session-level cache
ai_classifier_cache = {}

async def classify_domain_with_ai(domain: str, text_content: str):
    if domain in ai_classifier_cache:
        return ai_classifier_cache[domain]

    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY not found, skipping AI classification.")
        return {"is_product_for_sale": False, "confidence": "low"}

    truncated_content = text_content[:2000]
    
    prompt = f"""
    Analyze the following text from a website to determine if it was selling a product.
    Respond with ONLY a valid JSON object (no markdown, no preamble).
    
    The JSON object should have the following structure:
    {{
      "is_product_for_sale": true|false,
      "product_category": "string or null",
      "estimated_price_range": "string or null",
      "confidence": "high|medium|low"
    }}
    
    Website Text:
    {truncated_content}
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        # Clean the response to extract only the JSON part
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        result = json.loads(json_text)
        ai_classifier_cache[domain] = result
        return result
    except Exception as e:
        print(f"AI classification for {domain} failed: {e}")
        return {"is_product_for_sale": False, "confidence": "low"}
