import re
import asyncio
import aiohttp
import hashlib
from datetime import datetime

from src.celery_app import celery_app
from src.db import scans_collection
from src.risk_engine import calculate_risk_score
from src.log import get_scanner_logger
from src.email_service import send_osint_report

logger = get_scanner_logger()

# --- INPUT SANITIZATION ---
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

def is_safe_username(username: str) -> bool:
    if not username: 
        return False
    if not isinstance(username, str):
        return False
    return bool(USERNAME_PATTERN.match(username))



# --- CUSTOM HIGH-SPEED SCAN ENGINE ---
TARGET_SITES = {
    # --- Mainstream Social & Content ---
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Tumblr": "https://{}.tumblr.com",
    "YouTube": "https://www.youtube.com/@{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "Facebook": "https://www.facebook.com/{}",
    "VK": "https://vk.com/{}",
    "Telegram": "https://t.me/{}",
    
    # --- Tech, Dev & InfoSec ---
    "GitLab": "https://gitlab.com/{}",
    "Dev.to": "https://dev.to/{}",
    "Replit": "https://replit.com/@{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "LeetCode": "https://leetcode.com/{}/",
    "HackerRank": "https://www.hackerrank.com/{}",
    "Kaggle": "https://www.kaggle.com/{}",
    "TryHackMe": "https://tryhackme.com/p/{}",
    "Keybase": "https://keybase.io/{}",
    "Pastebin": "https://pastebin.com/u/{}",
    
    # --- Design & Freelance ---
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Flickr": "https://www.flickr.com/people/{}/",
    "Fiverr": "https://www.fiverr.com/{}",
    "About.me": "https://about.me/{}",
    "CodePen": "https://codepen.io/{}",
    
    # --- Creators, Blogs & Writing ---
    "Medium": "https://medium.com/@{}",
    "Patreon": "https://www.patreon.com/{}",
    "Linktree": "https://linktr.ee/{}",
    "Vimeo": "https://vimeo.com/{}",
    "WordPress": "https://{}.wordpress.com",
    "Blogger": "https://{}.blogspot.com",
    "Wattpad": "https://www.wattpad.com/user/{}",
    "Substack": "https://{}.substack.com",
    "Quora": "https://www.quora.com/profile/{}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    
    # --- Gaming, Music & Entertainment ---
    "Twitch": "https://www.twitch.tv/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Steam": "https://steamcommunity.com/id/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "MyAnimeList": "https://myanimelist.net/profile/{}",
    
    # --- Tipping & Finance ---
    "CashApp": "https://cash.app/${}",
    "Venmo": "https://account.venmo.com/u/{}",
    "BuyMeACoffee": "https://www.buymeacoffee.com/{}",
    "Ko-fi": "https://ko-fi.com/{}"
}






async def check_single_site(session, site_name, url_template, username):
    """Hits a single website concurrently to see if the profile exists."""
    url = url_template.format(username)
    try:
        # Strict 3-second timeout so one bad site doesn't hold up the line
        async with session.get(url, timeout=3) as response:
            if response.status == 200:
                return {"source": site_name, "exists": True, "url": url}
    except Exception:
        # If it times out or fails to connect, we just ignore it
        pass
    return None



async def check_gravatar(session, email: str):
    """Hashes the email and checks Gravatar for a linked OSINT profile."""
    if not email:
        return None
    
    # 1. Sanitize: Remove spaces and force lowercase
    clean_email = email.strip().lower()
    
    # 2. Hash: Convert to MD5
    email_hash = hashlib.md5(clean_email.encode('utf-8')).hexdigest()
    
    # 3. Pull the JSON OSINT data
    url = f"https://en.gravatar.com/{email_hash}.json"
    
    try:
        # Gravatar requires a User-Agent or they block the request
        headers = {'User-Agent': 'ShadowLink-OSINT-Tool/1.0'}
        async with session.get(url, headers=headers, timeout=3) as response:
            if response.status == 200:
                data = await response.json()
                if data and "entry" in data and len(data["entry"]) > 0:
                    profile = data["entry"][0]
                    return {
                        "source": "Gravatar (Email Linked)",
                        "exists": True,
                        "url": profile.get("profileUrl", f"https://en.gravatar.com/{email_hash}"),
                        # We grab the profile picture to display in your UI later!
                        "avatar_url": profile.get("thumbnailUrl", "") 
                    }
    except Exception as e:
        pass # Ignore timeouts or if the profile doesn't exist
        
    return None



async def blast_all_sites(username: str, email: str = None) -> list:
    """Fires off all requests at the exact same time, including Gravatar."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Add the 13 social media sites to the firing line
        if username:
            tasks.extend([check_single_site(session, name, url, username) for name, url in TARGET_SITES.items()])
        
        # Add Gravatar to the firing line if an email was provided
        if email:
            tasks.append(check_gravatar(session, email))
            
        # Run them ALL concurrently
        results = await asyncio.gather(*tasks)
        
        # Filter out the empty ones
        return [res for res in results if res is not None]


# --- MAIN CELERY TASK ---
@celery_app.task(name="perform_scan")
def perform_scan(scan_id: str, username: str = None, email: str = None) -> bool:
    try:
        logger.info("[TASK-%s] Starting high-speed scan task", scan_id)
        
        target_username = username

        if not target_username and email:
            if "@" not in email:
                logger.error("[TASK-%s] Invalid email format: %s", scan_id, email)
                raise ValueError("Invalid email format")
            target_username = email.split("@")[0]
            logger.info("[TASK-%s] Extracted username '%s' from email '%s'", scan_id, target_username, email)

        if not target_username and not email:
            logger.error("[TASK-%s] No valid username or email provided", scan_id)
            raise ValueError("No valid username or email provided")

        if not is_safe_username(target_username):
            logger.error("[TASK-%s] Unsafe characters in username: %s", scan_id, target_username)
            raise ValueError(f"Unsafe characters in username: {target_username}")

        logger.info("[TASK-%s] Starting scan for: %s", scan_id, target_username)
        
        # 1. Update Status to running
        try:
            scans_collection.update_one(
                {"scan_id": scan_id},
                {"$set": {"status": "running", "timestamp": datetime.utcnow()}}
            )
            logger.debug("[TASK-%s] Updated scan status to running", scan_id)
        except Exception as e:
            logger.error("[TASK-%s] Failed to update scan status: %s", scan_id, str(e))
            raise RuntimeError(f"Failed to update scan status: {str(e)}")

        # 2. EXECUTE THE ASYNC BLAST
        logger.debug("[TASK-%s] Firing high-speed async scanner...", scan_id)
        
        # asyncio.run bridges our synchronous Celery worker with our async engine
        results_list = asyncio.run(blast_all_sites(target_username, email))

        logger.info(f"High-speed engine found {len(results_list)} matches.")

        # 3. RISK ENGINE
        risk_data = calculate_risk_score(results_list)
        logger.info(f"Risk Score calculated: {risk_data['risk_score']} ({risk_data['risk_level']})")

        # 4. SAVE RESULTS
        scans_collection.update_one(
            {"scan_id": scan_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "results": results_list,
                    "found_count": len(results_list),
                    "risk_score": risk_data["risk_score"],
                    "risk_level": risk_data["risk_level"],
                    "scan_summary": risk_data["scan_summary"]
                }
            }
        )

        logger.info(f"Scan {scan_id} successfully finished. Found {len(results_list)} profiles.")
        # 5. DISPATCH THE EMAIL REPORT
        logger.info(f"[TASK-{scan_id}] Preparing to dispatch email report...")
        
        # We only send the email if the user actually provided one in the request!
        if email:
            email_sent = send_osint_report(
                recipient_email=email, 
                target_name=target_username, 
                results=results_list, 
                risk_score=risk_data["risk_score"], 
                risk_level=risk_data["risk_level"]
            )
            if email_sent:
                logger.info(f"[TASK-{scan_id}] Email report successfully dispatched to {email}")
            else:
                logger.warning(f"[TASK-{scan_id}] Email dispatch failed.")
        else:
            logger.info(f"[TASK-{scan_id}] No email provided in request. Skipping email dispatch.")

        logger.info(f"Scan {scan_id} successfully finished. Found {len(results_list)} profiles.")
        return True

    except Exception as e:
        # --- THE MASTER CATCH-ALL ---
        logger.error(f"Unexpected worker crash during scan {scan_id}: {str(e)}", exc_info=True)
        scans_collection.update_one(
            {"scan_id": scan_id},
            {
                "$set": {
                    "status": "failed", 
                    "scan_summary": f"Worker crashed: {str(e)}"
                }
            }
        )
        return False