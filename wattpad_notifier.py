import os
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ========================
# CONFIGURATION
# ========================
WATTPAD_USERNAME = "wlwsports"

# SMS Gateway Mapping (Free Email-to-SMS)
# Canada Examples:
# Bell/MTS: 2043830396@text.mts.net OR 2043830396@txt.bell.ca
# Rogers:   2043830396@pcs.rogers.com
# Telus:    2043830396@msg.telus.com
# Koodo:    2043830396@msg.koodomobile.com
# Fido:     2043830396@fido.ca
# Virgin:   2043830396@vmobile.ca
PHONE_EMAIL = "2043830396@msg.telus.com"  # <--- Replace 'yourcarrier.ca' with your specific carrier gateway

# Email to send FROM (e.g. a Gmail account)
SENDER_EMAIL = "8emilyfehr@gmail.com"  # <--- Change this to your sender email
SENDER_PASSWORD = "nyhuejmpcxpvruel"  # <--- Change this to your sender email app password

# Data storage file
STATS_FILE = "wattpad_stats.json"

def get_wattpad_stats(username):
    url = f"https://www.wattpad.com/api/v3/users/{username}/stories"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    res.raise_for_status()
    data = res.json()
    
    total_reads = 0
    total_votes = 0
    total_comments = 0
    
    if 'stories' in data:
        for story in data['stories']:
            total_reads += story.get('readCount', 0)
            total_votes += story.get('voteCount', 0)
            total_comments += story.get('commentCount', 0)
            
    return {
        "reads": total_reads,
        "votes": total_votes,
        "comments": total_comments
    }

def send_sms(message):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = PHONE_EMAIL
        
        # Add the message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP (change if using another email provider)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Successfully sent SMS notification")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

def main():
    try:
        current_stats = get_wattpad_stats(WATTPAD_USERNAME)
    except Exception as e:
        print(f"Error fetching Wattpad data: {e}")
        return

    # Load previous stats
    previous_stats = {"reads": 0, "votes": 0, "comments": 0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                previous_stats = json.load(f)
        except Exception:
            pass

    # Calculate differences (readers that day)
    new_reads = current_stats["reads"] - previous_stats.get("reads", 0)
    new_votes = current_stats["votes"] - previous_stats.get("votes", 0)
    
    if new_reads < 0: new_reads = 0
    if new_votes < 0: new_votes = 0

    # Format SMS
    # Keep it short for SMS
    sms_text = (
        f"Wattpad Daily Stats:\n"
        f"Reads: {current_stats['reads']} (+{new_reads})\n"
        f"Votes: {current_stats['votes']} (+{new_votes})"
    )
    
    print("Sending Notification:")
    print(sms_text)

    # Only send SMS if there's actually new reads/votes to report maybe? 
    # Or just send it daily regardless. Let's send daily.
    
    # Send SMS (commented out until credentials are provided)
    if "your_email" not in SENDER_EMAIL and "yourcarrier" not in PHONE_EMAIL:
        send_sms(sms_text)
    else:
        print("\n[!] Please update the EMAIL/SMS configuration in the script to actually send the SMS.")

    # Save current stats for tomorrow
    current_stats["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current_stats, f, indent=4)

if __name__ == "__main__":
    main()
