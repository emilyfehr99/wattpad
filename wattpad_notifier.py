"""
Daily Wattpad SMS Notifier for https://github.com/emilyfehr99/wattpad
Fetches Wattpad stats, includes today's ranks, sends via Email-to-SMS at 7 PM (GitHub Actions).
"""
import os
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ========================
# CONFIGURATION (override with env / GitHub Secrets)
# ========================
WATTPAD_USERNAME = os.environ.get("WATTPAD_USERNAME", "wlwsports")

# Email-to-SMS: send to your phone's carrier gateway (e.g. 2043830396@msg.telus.com)
# Set PHONE_EMAIL, SENDER_EMAIL, SENDER_PASSWORD in GitHub repo Secrets for Actions
PHONE_EMAIL = os.environ.get("PHONE_EMAIL", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wattpad_stats.json")


def get_wattpad_stats(username):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    user_url = f"https://www.wattpad.com/api/v3/users/{username}?fields=numFollowers"
    user_res = requests.get(user_url, headers=headers)
    user_res.raise_for_status()
    user_data = user_res.json()
    followers = user_data.get('numFollowers', 0)

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
            comments = story.get('commentCount', 0)
            parts = story.get('numParts', 0)
            completed = story.get('completed', False)

            total_reads += reads
            total_votes += votes
            total_comments += comments

            story_stats[title] = {
                "reads": reads,
                "votes": votes,
                "comments": comments,
                "parts": parts,
                "completed": completed
            }

    return {
        "followers": followers,
        "reads": total_reads,
        "votes": total_votes,
        "comments": total_comments,
        "stories": story_stats
    }


def get_rankings_from_stats_file():
    """Return rankings if stored in stats file (e.g. from manual update or future scraper)."""
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
        return data.get("rankings", {})
    except Exception:
        return {}


def send_sms(message):
    if not PHONE_EMAIL or not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Skipping SMS: set PHONE_EMAIL, SENDER_EMAIL, SENDER_PASSWORD (e.g. in GitHub Secrets)")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = PHONE_EMAIL
        msg['Subject'] = "Wattpad Update"
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Successfully sent SMS notification")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False


def main():
    try:
        current = get_wattpad_stats(WATTPAD_USERNAME)
    except Exception as e:
        print(f"Error fetching Wattpad data: {e}")
        return

    # Load previous stats (and any saved rankings)
    previous = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                previous = json.load(f)
        except Exception:
            pass

    # Use saved rankings if we have them (today's ranks)
    current["rankings"] = previous.get("rankings", {}) or get_rankings_from_stats_file()

    # Deltas
    new_followers = current["followers"] - previous.get("followers", current["followers"])
    new_reads = current["reads"] - previous.get("reads", current["reads"])
    new_votes = current["votes"] - previous.get("votes", current["votes"])
    new_comments = current["comments"] - previous.get("comments", current["comments"])

    # Story lines with deltas
    story_lines = []
    prev_stories = previous.get("stories", {})
    for title, stats in current["stories"].items():
        prev_s = prev_stories.get(title, stats)
        d_reads = stats["reads"] - prev_s.get("reads", stats["reads"])
        d_comments = stats["comments"] - prev_s.get("comments", stats["comments"])

        parts_info = f"({stats['parts']} Pts)"
        completion_info = " [Done!]" if stats['completed'] else ""
        line = f"{title}: {parts_info}{completion_info}"
        updates = []
        if d_reads > 0:
            updates.append(f"+{d_reads}R")
        if d_comments > 0:
            updates.append(f"+{d_comments}C")
        if updates:
            line += " " + ", ".join(updates)
        story_lines.append(line)

    # Build SMS (keep under ~160 chars per segment for SMS)
    dt_now = datetime.now().strftime("%m/%d %H:%M")
    sms_text = f"Wattpad Update ({dt_now}):\n"
    sms_text += f"GAINS: +{new_reads}R, +{new_votes}V, +{new_comments}C, +{new_followers}Fol\n"
    sms_text += f"TOTAL: {current['reads']}R, {current['followers']}Fol\n"

    # Today's ranks (if we have them in stats file)
    if current.get("rankings"):
        sms_text += "---\nTODAY'S RANKS:\n"
        for story_title, ranks in current["rankings"].items():
            if isinstance(ranks, dict):
                sms_text += f"{story_title}\n"
                for cat, rank in list(ranks.items())[:5]:
                    sms_text += f"  {cat}: {rank}\n"
            else:
                sms_text += f"{story_title}: {ranks}\n"

    if story_lines:
        sms_text += "---\n"
        sms_text += "\n".join(story_lines)

    print("Sending notification:")
    print(sms_text)

    send_sms(sms_text)

    # Persist for next run (including rankings)
    current["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current, f, indent=2)


if __name__ == "__main__":
    main()
