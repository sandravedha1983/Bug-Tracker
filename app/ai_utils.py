import logging
import os
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hugging Face Inference API settings
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HF_TOKEN = os.environ.get('HF_TOKEN') # User can add this to Vercel env vars

def predict_priority(description):
    """
    Predicts priority based on bug description.
    Uses Hugging Face API if token is present, otherwise falls back to robust keyword logic.
    """
    if not description:
        return "Medium"

    desc_lower = description.lower()
    
    # 1. Robust Keyword-based Triage (High-confidence fallback)
    high_priority_keywords = [
        'crash', 'outage', '500 error', 'security', 'leak', 'fatal', 
        'emergency', 'data loss', 'deleted', 'vulnerability', 'exploit',
        'cannot login', 'can\'t login', 'broken authentication', 'auth failure',
        'production down', 'system down', 'critical'
    ]
    
    low_priority_keywords = [
        'typo', 'color', 'font', 'ui', 'cosmetic', 'spacing', 'padding',
        'suggestion', 'feature request', 'improvement', 'minor'
    ]

    if any(kw in desc_lower for kw in high_priority_keywords):
        return "High"
    
    # 2. Attempt Hugging Face Inference API if token exists
    if HF_TOKEN:
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {
                "inputs": description,
                "parameters": {"candidate_labels": ["urgent priority", "normal task", "minor issue"]}
            }
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                top_label = result["labels"][0]
                logger.info(f"HF API Result: {top_label}")
                
                if "urgent" in top_label:
                    return "High"
                elif "normal" in top_label:
                    return "Medium"
                else:
                    return "Low"
            else:
                logger.warning(f"HF API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"HF API call failed: {e}")

    # 3. Keyword-based Medium/Low Fallback
    if any(kw in desc_lower for kw in low_priority_keywords):
        return "Low"
        
    return "Medium"

def generate_summary(description):
    """
    Generates a short summary of the description using intelligent truncation.
    """
    if not description:
        return ""
    
    # First sentence or first 100 chars
    sentences = description.split('.')
    if sentences:
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 100:
            return first_sentence[:97] + "..."
        if first_sentence:
            return first_sentence + "."
    
    return description[:100] + "..." if len(description) > 100 else description
