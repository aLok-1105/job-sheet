from parser import parse_job_message

def test_parsing():
    sample_text = """Virtusa 
Position: Java AWS Developer 
Qualifications: Bachelor's / Master’s Degree 
Experience: Experienced 
Location: Bangalore, India 
📌Apply Link: https://www.virtusa.com/careers/in/gurgaon/core-tech-java/java-aws-developer/creq250605 
👉WhatsApp Channel: https://whatsapp.com/channel/0029VaI5CV93AzNUiZ5Tt226 
👉Telegram Link: https://t.me/addlist/4q2PYC0pH_VjZDk5 
Like for more job opportunities ❤️"""

    result = parse_job_message(sample_text)
    print("Parsing Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
        
    assert result["company"] == "Virtusa"
    assert result["position"] == "Java AWS Developer"
    assert result["qualifications"] == "Bachelor's / Master’s Degree"
    assert result["experience"] == "Experienced"
    assert result["location"] == "Bangalore, India"
    assert result["apply_link"] == "https://www.virtusa.com/careers/in/gurgaon/core-tech-java/java-aws-developer/creq250605"
    print("Test passed successfully!")

if __name__ == "__main__":
    test_parsing()
