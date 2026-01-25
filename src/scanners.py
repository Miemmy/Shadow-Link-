import subprocess
import sys
import re
import os
from datetime import datetime
from celery_app import celery_app
from db import scans_collection

# to sanitize input
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

def is_safe_username(username: str) -> bool:
    if not username: return False
    return bool(USERNAME_PATTERN.match(username))

@celery_app.task(name="perform_scan")
def perform_scan(scan_id: str, username: str =None, email:str = None) -> bool:

    target_username= username 

    if not target_username and email:
        target_username= email.split("@")[0]
        print(f"[WORKER] Extracted username '{target_username}' from email '{email}'")

    if not target_username:
        print("[ERROR] No valid username or email provided.")
        return False

    print(f"[WORKER] Starting Stream-Scan for: {target_username}")
    
    # 1. Update Status
    scans_collection.update_one(
        {"scan_id": scan_id},
        {"$set": {"status": "running", "timestamp": datetime.utcnow()}}
    )

    if not is_safe_username(target_username):
        print(f"[ERROR] Unsafe characters in username: {target_username}")
        return False

    results_list = []

    try:
        # --- LOCATE SHERLOCK ---
        sherlock_path = os.path.join(sys.prefix, "Scripts", "sherlock.exe")
        if not os.path.exists(sherlock_path):
             sherlock_path = "sherlock"

        
        # we add --no-color so we get clean text we can  easily read
        command = [
            sherlock_path,
            target_username,
            "--timeout", "5",
            "--print-found",
            "--no-color" 
        ]

        print(f"[DEBUG] Running command: {command}")

        # Run and catch the output text directly
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        
        raw_output = process.stdout
        
        # --- PARSE THE TEXT OUTPUT ---
        # Sherlock prints lines like: "[+] GitHub: https://github.com/torvalds"
        # We use Regex to grab the Name and the URL.
        # Pattern: Look for "[+]", then a Name, then ": ", then a URL.

        regex_pattern = r"\[\+\]\s*([^:]+):\s*(https?://\S+)"
        
        matches = re.findall(regex_pattern, raw_output)
        
        for name, url in matches:
            results_list.append({
                "source": name.strip(),
                "exists": True,
                "url": url.strip()
            })

        print(f"[SUCCESS] Regex found {len(results_list)} matches in output.")

        
        if len(results_list) == 0:
            print("[DIAGNOSTIC] stdout content (First 500 chars):")
            print(raw_output[:500])
            print("[DIAGNOSTIC] stderr content:")
            print(process.stderr)

    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")

    # saving results
    scans_collection.update_one(
        {"scan_id": scan_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "results": results_list,
                "found_count": len(results_list)
            }
        }
    )

    print(f"[WORKER] Finished. Found {len(results_list)}.")
    return True