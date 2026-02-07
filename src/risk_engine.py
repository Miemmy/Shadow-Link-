# 1. Social Media (Identity Theft Risk)
# revealing personal details, family, location, DOB.
HIGH_EXPOSURE_SITES = [
    "Facebook", "Instagram", "Twitter", "X", "TikTok", 
    "Snapchat", "Pinterest", "Flickr", "Tumblr", "Venmo"
]

# 2. Professional (Phishing/Career Risk)
# revealing employer, email formats, technologies used.
PROFESSIONAL_SITES = [
    "LinkedIn", "GitHub", "GitLab", "AngelList", "Upwork", 
    "Freelancer", "StackOverflow", "Trello"
]

# 3. Sensitive (Reputation & Security Risk)
# Sites associated with breaches, hacking, adult content, or leaks.
SENSITIVE_SITES = [
    "Pastebin", "Pornhub", "Xvideos", "RedTube", "CamModels",
    "HackForums", "Cracked", "Nulled", "RaidForums", "AnonFiles"
]

from typing import List, Dict


def calculate_risk_score(results: List[Dict])-> Dict:
    score=0
    found_sites_names=[result["source"] for result in results ]
    #base score: I point per site found
    account_count= len(results)
    score+= account_count

    #weighted score for certain sites
    social_count = 0
    pro_count = 0
    sensitive_count = 0

    for site in found_sites_names:
        if site in SENSITIVE_SITES:
            sensitive_count += 1
            score+=20 

        elif site in HIGH_EXPOSURE_SITES:
            score+=10
            social_count += 1

        elif site in PROFESSIONAL_SITES:
            pro_count += 1
            score+=5
    
    final_score=min(score,100)

    if final_score < 20:
        level=" LOW "
    elif final_score < 65:
        level="MEDIUM"
    else:
        level=" HIGH "

    summary= f"Found {account_count} profiles. Includes {social_count} social, {pro_count} professional, and {sensitive_count} sensitive accounts."

    

    return {
        "risk_score": final_score,
        "risk_level": level,
        "scan_summary": summary
    }




