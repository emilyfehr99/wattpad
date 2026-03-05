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
# Telus:    number@msg.telus.com
# Rogers:   number@pcs.rogers.com
# Bell/MTS: number@text.mts.net OR number@txt.bell.ca
PHONE_EMAIL = "2043830396@msg.telus.com"

# Email to send FROM (e.g. 8emilyfehr@gmail.com)
SENDER_EMAIL = "8emilyfehr@gmail.com"
SENDER_PASSWORD = "nyhuejmpcxpvruel"

# Data storage file
STATS_FILE = "wattpad_stats.json"

def get_wattpad_stats(username):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. Get User Profile (Followers)
    user_url = f"https://www.wattpad.com/api/v3/users/{username}?fields=numFollowers"
    user_res = requests.get(user_url, headers=headers)
    user_res.raise_for_status()
    user_data = user_res.json()
    followers = user_data.get('numFollowers', 0)
    
    # 2. Get Stories (Reads, Votes, Comments)
    stories_url = f"https://www.wattpad.com/api/v3/users/{username}/stories"
    stories_res = requests.get(stories_url, headers=headers)
    stories_res.raise_for_status()
    stories_data = stories_res.json()
    
    total_reads = 0
    total_votes = 0
    total_comments = 0
    story_stats = {}
    
    if 'stories' in stories_data:
        for story in stories_data['stories']:
            title = story.get('title', 'Unknown')
            reads = story.get('readCount', 0)
            votes = story.get('voteCount', 0)
            
            total_reads += reads
            total_votes += votes
            total_comments += story.get('commentCount', 0)
            
            story_stats[title] = {
                "reads": reads,
                "votes": votes
            }
            
    return {
        "followers": followers,
        "reads": total_reads,
        "votes": total_votes,
        "comments": total_comments,
        "stories": story_stats
    }

def send_sms(message):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = PHONE_EMAIL
        msg.attach(MIMEText(message, 'plain'))
        
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
        current = get_wattpad_stats(WATTPAD_USERNAME)
    except Exception as e:
        print(f"Error fetching Wattpad data: {e}")
        return

    # Load previous stats
    previous = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                previous = json.load(f)
        except Exception:
            pass

    # DELTAS
    new_followers = current["followers"] - previous.get("followers", current["followers"])
    new_reads = current["reads"] - previous.get("reads", current["reads"])
    new_votes = current["votes"] - previous.get("votes", current["votes"])

    # STORY DELTAS (Optional but cool if they have multiple)
    story_lines = []
    prev_stories = previous.get("stories", {})
    for title, stats in current["stories"].items():
        prev_s = prev_stories.get(title, {"reads": stats["reads"]})
        d_reads = stats["reads"] - prev_s["reads"]
        if d_reads > 0:
            story_lines.append(f"{title}: +{d_reads}")

    # Format SMS
    # Keep it short!
    sms_text = f"Wattpad Daily:\n"
    sms_text += f"GAINS: +{new_reads} Reads, +{new_votes} Votes, +{new_followers} Fol\n"
    sms_text += f"---\n"
    sms_text += f"TOTAL: {current['reads']} Reads, {current['followers']} Fol\n"
    
    if story_lines:
        sms_text += f"---\n"
        sms_text += "\n".join(story_lines)

    print("Sending Notification:")
    print(sms_text)

    # Send Notification
    if "your_email" not in SENDER_EMAIL:
        send_sms(sms_text)

    # Save for tomorrow
    current["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current, f, indent=4)

if __name__ == "__main__":
    main()
