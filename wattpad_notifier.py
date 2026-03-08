import os
import smtplib
import json
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================
# CONFIGURATION (same as original; for GitHub Actions use Secrets)
# ========================
WATTPAD_USERNAME = os.environ.get("WATTPAD_USERNAME", "wlwsports")

# Set in script here for local, or as repo Secrets (PHONE_EMAIL, SENDER_EMAIL, SENDER_PASSWORD) for Actions
PHONE_EMAIL = os.environ.get("PHONE_EMAIL", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

STATS_FILE = "wattpad_stats.json"


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
            story_id = story.get('id')
            reads = story.get('readCount', 0)
            votes = story.get('voteCount', 0)
            comments = story.get('commentCount', 0)
            parts = story.get('numParts', 0)
            completed = story.get('completed', False)

            total_reads += reads
            total_votes += votes
            total_comments += comments

            story_stats[title] = {
                "id": story_id,
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


def fetch_story_parts(story_id, headers):
    """Fetch parts (chapters) with create/publish dates for key times. Returns list of {title, createDate}."""
    if not story_id:
        return []
    try:
        # Try fields that might return part dates (API varies)
        url = f"https://www.wattpad.com/api/v3/stories/{story_id}?fields=parts(id,title,createDate)"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        parts = data.get("parts") or []
        out = []
        for p in parts:
            # createDate might be ISO string or ms timestamp
            created = p.get("createDate") or p.get("create_date") or p.get("publishedDate")
            if created:
                out.append({"title": p.get("title", ""), "createDate": created})
            else:
                out.append({"title": p.get("title", ""), "createDate": None})
        return out
    except Exception:
        return []


def format_key_times(story_title, parts_with_dates, prev_part_count):
    """Build a short 'key times' line: last chapter date, new parts since last run."""
    if not parts_with_dates:
        return None
    lines = []
    # Last chapter date
    with_dates = [p for p in parts_with_dates if p.get("createDate")]
    if with_dates:
        last = with_dates[-1]
        raw = last["createDate"]
        try:
            if isinstance(raw, (int, float)):
                dt = datetime.utcfromtimestamp(raw / 1000.0 if raw > 1e10 else raw)
            else:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            last_str = dt.strftime("%b %d")
            lines.append(f"Last ch: {last_str}")
        except Exception:
            pass
    # New parts since last run
    curr_count = len(parts_with_dates)
    if prev_part_count is not None and curr_count > prev_part_count:
        new = curr_count - prev_part_count
        lines.append(f"+{new} new pt(s)")
    # Fallback: at least show part count when we have parts
    if not lines and parts_with_dates:
        lines.append(f"{curr_count} pts")
    return " | ".join(lines) if lines else None


def send_sms(message):
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
    except Exception as e:
        print(f"Failed to send SMS: {e}")


def main():
    try:
        current = get_wattpad_stats(WATTPAD_USERNAME)
    except Exception as e:
        print(f"Error fetching Wattpad data: {e}")
        return

    previous = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                previous = json.load(f)
        except Exception:
            pass

    # Keep saved rankings so they appear in the message (API doesn't return them)
    current["rankings"] = previous.get("rankings", {})
    prev_stories = previous.get("stories", {})

    # Fetch part/chapter dates for key times (last chapter, new parts)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    key_times_lines = []
    for title, stats in current["stories"].items():
        story_id = stats.get("id")
        parts_with_dates = fetch_story_parts(story_id, headers)
        prev_part_count = prev_stories.get(title, {}).get("parts") if title in prev_stories else None
        line = format_key_times(title, parts_with_dates, prev_part_count)
        if line:
            key_times_lines.append(f"{title}: {line}")
        # Store for next run (part count; optional: part dates)
        if parts_with_dates:
            stats["part_count"] = len(parts_with_dates)
            stats["last_part_date"] = None
            with_dates = [p for p in parts_with_dates if p.get("createDate")]
            if with_dates:
                raw = with_dates[-1]["createDate"]
                try:
                    if isinstance(raw, (int, float)):
                        dt = datetime.utcfromtimestamp(raw / 1000.0 if raw > 1e10 else raw)
                    else:
                        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                    stats["last_part_date"] = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

    new_followers = current["followers"] - previous.get("followers", current["followers"])
    new_reads = current["reads"] - previous.get("reads", current["reads"])
    new_votes = current["votes"] - previous.get("votes", current["votes"])
    new_comments = current["comments"] - previous.get("comments", current["comments"])

    story_lines = []
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

    dt_now = datetime.now().strftime("%m/%d %H:%M")
    sms_text = f"Wattpad Update ({dt_now}):\n"
    sms_text += f"GAINS: +{new_reads}R, +{new_votes}V, +{new_comments}C, +{new_followers}Fol\n"
    sms_text += f"---\n"
    sms_text += f"TOTAL: {current['reads']}R, {current['followers']}Fol\n"

    # Key times: last chapter date, new parts since last run
    if key_times_lines:
        sms_text += "---\nKEY TIMES:\n"
        sms_text += "\n".join(key_times_lines) + "\n"

    # Today's ranks (add to message when present in stats file)
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

    if "your_email" not in SENDER_EMAIL:
        send_sms(sms_text)

    current["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current, f, indent=4)


if __name__ == "__main__":
    main()
