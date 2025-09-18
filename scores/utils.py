import csv
import difflib
from io import TextIOWrapper
import json
from google import genai
from django.conf import settings


# In-memory storage
LEADS = []

def parse_leads_csv(file):
    """
    file: UploadedFile from Django request.FILES
    Returns: list of leads as dicts
    """
    global LEADS
    LEADS = []  # reset previous leads
    
    # Convert file to a text wrapper (CSV reader needs text, not bytes)
    file_wrapper = TextIOWrapper(file.file, encoding='utf-8')
    reader = csv.DictReader(file_wrapper)
    
    for row in reader:
        # Ensure all required fields exist
        lead = {
            'name': row.get('name', '').strip(),
            'role': row.get('role', '').strip(),
            'company': row.get('company', '').strip(),
            'industry': row.get('industry', '').strip(),
            'location': row.get('location', '').strip(),
            'linkedin_bio': row.get('linkedin_bio', '').strip(),
        }
        LEADS.append(lead)
    
    return LEADS

# Role relevance mapping
ROLE_SCORE = {
    'decision_maker': 20,
    'influencer': 10,
    'others': 0
}

# Industry match function
def industry_match(lead_industry, ideal_use_cases):
    lead_industry = lead_industry.lower().strip()
    
    for uc in ideal_use_cases:
        uc = uc.lower().strip()
        
        # Exact match
        if lead_industry == uc:
            return 20
        
        # Substring overlap match
        if lead_industry in uc or uc in lead_industry:
            return 10
        
        # Fuzzy match (e.g: "fintech" vs "financial services")
        similarity = difflib.SequenceMatcher(None, lead_industry, uc).ratio()
        if similarity > 0.75:  # Can be tuned
            return 10
    
    return 0

# Rule Layer scoring
def calculate_rule_score(lead, offer):
    score = 0
    # Role relevance
    role = lead[0]['role'].lower()
    if any(x in role for x in ['ceo', 'founder', 'head', 'vp', 'director','coo', 'cto', 'cfo']):
        score += ROLE_SCORE['decision_maker']
    elif any(x in role for x in ['manager', 'specialist', 'tech lead', 'sales head']):
        score += ROLE_SCORE['influencer']
    else:
        score += ROLE_SCORE['others']

    # Industry match
    score += industry_match(lead[0]['industry'], offer['ideal_use_cases'])

    # Data completeness
    if all(lead[0].values()):
        score += 10
    
    return score 


# -----------------------------
# AI Layer
# -----------------------------
def ai_intent_score(lead, offer):
    """
    Call AI model to classify intent (High/Medium/Low)
    Returns: ai_points (int) and reasoning (str)
    """
    prompt = f"""
You are a sales assistant. 
Given the product/offer details: {offer}
And the lead info: {lead}

Classify the buying intent of this lead as High, Medium, or Low.
Also, provide 1-2 sentence reasoning.
Respond ONLY in JSON like:
{{"intent": "<High/Medium/Low>", "reasoning": "<reasoning>" }}
    """
    
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY  # Replace with actual key
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )

    text= (
                response.text
                if response.text
                else "No response from AI."
            )
    
    # Clean and parse JSON response
    text_clean = text.replace("```json\n", "").replace("\n```", "").strip()
    data = json.loads(text_clean)

    # Extract intent and reasoning
    result = {
        "intent": data["intent"],
        "reasoning": data["reasoning"]
    }

    # Map intent to points
    intent_map = {"High": 50, "Medium": 30, "Low": 10}
    ai_points = intent_map.get(result.get("intent", "Medium"), 30)

    return ai_points, result.get("reasoning", "")


# -----------------------------
# Final combined scoring
# -----------------------------
def final_score(lead, offer):
    """
    Computes rule score + AI score and returns full result
    """
    rule_points = calculate_rule_score(lead, offer)
    ai_points, reasoning = ai_intent_score(lead, offer)
    total_score = rule_points + ai_points

    # Determine final intent label
    if total_score >= 70:
        intent = "High"
    elif total_score >= 40:
        intent = "Medium"
    else:
        intent = "Low"

    return {
        "name": lead[0]['name'],
        "role": lead[0]['role'],
        "company": lead[0]['company'],
        "intent": intent,
        "score": total_score,
        "reasoning": reasoning
    }
