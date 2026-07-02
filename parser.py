import re
from typing import Dict, Optional

def parse_job_message(text: str) -> Optional[Dict[str, str]]:
    """
    Parses a Telegram job posting message and extracts:
    - Company Name
    - Position
    - Qualifications
    - Experience
    - Location
    - Apply Link
    
    Returns a dictionary of fields, or None if the message doesn't appear to be a job posting.
    """
    if not text or not text.strip():
        return None
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return None

    # Extracted fields initialized
    company = ""
    position = ""
    qualifications = ""
    experience = ""
    location = ""
    apply_link = ""

    # Patterns for key-value matching (case-insensitive)
    pos_pattern = re.compile(r'(?:position|role|job title|title)\s*:\s*(.*)', re.IGNORECASE)
    qual_pattern = re.compile(r'(?:qualifications|qualification|degree|eligible|eligibility|education)\s*:\s*(.*)', re.IGNORECASE)
    exp_pattern = re.compile(r'(?:experience|exp)\s*:\s*(.*)', re.IGNORECASE)
    loc_pattern = re.compile(r'(?:location|job location|work location)\s*:\s*(.*)', re.IGNORECASE)
    
    # Emojis or symbols could prefix the label, so we search for standard keywords
    apply_pattern = re.compile(r'(?:apply\s*link|apply\s*here|apply|registration\s*link|register\s*link)\s*:\s*(https?://\S+)', re.IGNORECASE)

    # 1. Identify all URLs in the message text
    urls = re.findall(r'(https?://\S+)', text)
    apply_candidates = []
    for url in urls:
        # Clean trailing symbols, emojis, or punctuation from the URL
        clean_url = url.rstrip('👉📌🔗❤️.()[]{} \t\n\r')
        # Filter out WhatsApp and Telegram channel links to avoid picking promo links
        if not any(domain in clean_url.lower() for domain in ['t.me', 'telegram', 'whatsapp.com', 'chat.whatsapp']):
            apply_candidates.append(clean_url)

    # 2. Extract fields by searching line by line
    for line in lines:
        # Position
        pos_match = pos_pattern.search(line)
        if pos_match:
            position = pos_match.group(1).strip()
            continue
            
        # Qualifications
        qual_match = qual_pattern.search(line)
        if qual_match:
            qualifications = qual_match.group(1).strip()
            continue
            
        # Experience
        exp_match = exp_pattern.search(line)
        if exp_match:
            experience = exp_match.group(1).strip()
            continue
            
        # Location
        loc_match = loc_pattern.search(line)
        if loc_match:
            location = loc_match.group(1).strip()
            continue

        # Apply Link
        apply_match = apply_pattern.search(line)
        if apply_match:
            candidate = apply_match.group(1).strip().rstrip('👉📌🔗❤️.()[]{} \t\n\r')
            if not any(domain in candidate.lower() for domain in ['t.me', 'telegram', 'whatsapp.com', 'chat.whatsapp']):
                apply_link = candidate
                continue

    # 3. Fallback for apply link: use the first non-social URL candidate if not found explicitly
    if not apply_link and apply_candidates:
        apply_link = apply_candidates[0]

    # 4. Extract Company Name
    # We check if the very first line of the message is a non-empty, non-label, non-URL line
    if lines:
        first_line = lines[0]
        is_label_or_link = (
            pos_pattern.search(first_line) or 
            qual_pattern.search(first_line) or 
            exp_pattern.search(first_line) or 
            loc_pattern.search(first_line) or 
            apply_pattern.search(first_line) or
            'http://' in first_line.lower() or 
            'https://' in first_line.lower()
        )
        if not is_label_or_link and len(first_line) < 100:
            # Clean emojis and whitespace from the company name
            company = first_line.strip('📌👉🔗❤️ \t\n\r')

    # If we have neither a position nor an apply link, it's probably not a job post
    if not position and not apply_link:
        return None

    return {
        "company": company or "N/A",
        "position": position or "N/A",
        "qualifications": qualifications or "N/A",
        "experience": experience or "N/A",
        "location": location or "N/A",
        "apply_link": apply_link or "N/A"
    }
