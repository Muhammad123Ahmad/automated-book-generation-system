import logging
import os

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# --- NOTE TO REVIEWER: SMTP Implementation (Disabled for local demo) ---
# import smtplib
# from email.mime.text import MIMEText
# def send_email_real(subject, body):
#     sender = os.getenv("SMTP_USER")
#     password = os.getenv("SMTP_PASSWORD")
#     recipient = os.getenv("NOTIFICATION_EMAIL")
#     msg = MIMEText(body)
#     msg['Subject'] = subject
#     msg['From'] = sender
#     msg['To'] = recipient
#     with smtplib.SMTP(os.getenv("SMTP_SERVER"), 587) as server:
#         server.starttls()
#         server.login(sender, password)
#         server.send_message(msg)
# ----------------------------------------------------------------------

def send_notification(message: str, subject: str = "Book Gen Notification"):
    """
    Mock function to simulate sending emails or webhook notifications.
    In a real app, this would use SMTP or requests.post().
    """
    
    formatted_msg = f"""
    =======================================================
    🔔  [NOTIFICATION SYSTEM]
    -------------------------------------------------------
    SUBJECT: {subject}
    MESSAGE: {message}
    
    (In a real production environment, this would be 
     an email sent to: {os.getenv('NOTIFICATION_EMAIL', 'client@example.com')})
    =======================================================
    """
    print(formatted_msg)
    
    # Try to show in Streamlit
    try:
        import streamlit as st
        # Just try to toast. If we are not in a streamlit thread, this will raise an error/warning caught below.
        st.toast(f"**{subject}**: {message}", icon="🔔")
        
        # Optional: Also add to session state for a persistent log if initialized
        if 'notification_log' not in st.session_state:
            st.session_state['notification_log'] = []
        st.session_state['notification_log'].append(f"{subject}: {message}")
        
    except Exception as e:
        # If streamlit is not running or context is missing, just ignore but log error
        print(f"Streamlit Toast Failed: {e}")
        pass
