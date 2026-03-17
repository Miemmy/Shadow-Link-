import smtplib
import os
from email.message import EmailMessage
from src.log import get_scanner_logger

logger = get_scanner_logger()

def send_osint_report(recipient_email: str, target_name: str, results: list, risk_score: int, risk_level: str) -> bool:
    """Generates a professional HTML report and emails it to the user."""
    
    if not recipient_email:
        logger.warning("No recipient email provided, skipping email dispatch.")
        return False

    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        logger.error("SMTP credentials missing in .env file. Cannot send email.")
        return False

    # --- 1. BUILD THE HTML EMAIL ---
    msg = EmailMessage()
    msg['Subject'] = f"ShadowLink OSINT Report: {target_name}"
    msg['From'] = f"ShadowLink Engine <{sender_email}>"
    msg['To'] = recipient_email

    # Format the links into a clean HTML list
    results_html = "".join([
        f"<li style='margin-bottom: 8px;'><b>{r.get('source', 'Unknown')}:</b> <a href='{r.get('url', '#')}' style='color: #3498db; text-decoration: none;'>{r.get('url', 'N/A')}</a></li>"
        for r in results
    ])

    # The HTML Template (Dark mode inspired!)
    html_content = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 4px solid #2c3e50;">
                
                <h2 style="color: #2c3e50; margin-top: 0;">ShadowLink Intelligence Report</h2>
                <p style="color: #555; font-size: 16px;">Target Scan: <strong>{target_name}</strong></p>
                
                <div style="background-color: #f8d7da; color: #721c24; padding: 12px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <strong style="font-size: 18px;">Risk Score: {risk_score}/100</strong> ({risk_level})
                </div>
                
                <h3 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 8px;">Discovered Profiles:</h3>
                <ul style="list-style-type: none; padding-left: 0;">
                    {results_html}
                </ul>
                
                <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;" />
                <p style="font-size: 12px; color: #999; text-align: center;">
                    Generated automatically by the ShadowLink OSINT Engine.<br>
                    CONFIDENTIAL DATA
                </p>
            </div>
        </body>
    </html>
    """
    
    msg.set_content("Please enable HTML to view this report.")
    msg.add_alternative(html_content, subtype='html')

    # --- 2. SEND THE EMAIL ---
    try:
        # Connect to Gmail's secure SMTP server
        logger.debug(f"Connecting to SMTP server to email {recipient_email}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            
        logger.info(f"Successfully emailed OSINT report to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False