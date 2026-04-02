import os
import re
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
# Telus: number@msg.telus.com
# Rogers: number@pcs.rogers.com
# Bell/MTS: number@text.mts.net OR number@txt.bell.ca
PHONE_EMAIL = "2043830396@msg.telus.com"

# Email credentials (Gmail app password)
SENDER_EMAIL = "8emilyfehr@gmail.com"
SENDER_PASSWORD = "nyhuejmpcxpvruel"

# Data storage file (persisted in GitHub repository)
STATS_FILE = "wattpad_stats.json"


def get_wattpad_stats(username, session=None):
    """Fetch basic user and story stats via Wattpad's v3 API."""
    stats = {
        "followers": 0,
        "reads": 0,
        "votes": 0,
        "comments": 0,
        "stories": {},
        "engaged_readers": 0 # qualifiedUniqueReaders
    }
    
    try:
        # User stats
        user_url = f"https://www.wattpad.com/api/v3/users/{username}"
        r = session.get(user_url, timeout=10) if session else requests.get(user_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            stats["followers"] = data.get("numFollowers", 0)

        # Stories stats for user
        # Note: qualifiedUniqueReaders requires authentication (session)
        fields = "stories(id,title,readCount,voteCount,commentCount,numParts,completed,qualifiedUniqueReaders)"
        stories_url = f"https://www.wattpad.com/api/v3/users/{username}/stories?fields={fields}&limit=15"
        
        r = session.get(stories_url, timeout=10) if session else requests.get(stories_url, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            for story in data.get("stories", []):
                title = story.get("title")
                stats["stories"][title] = {
                    "id": story.get("id"),
                    "reads": story.get("readCount", 0),
                    "votes": story.get("voteCount", 0),
                    "comments": story.get("commentCount", 0),
                    "parts": story.get("numParts", 0),
                    "completed": story.get("completed", False),
                    "engaged": story.get("qualifiedUniqueReaders", 0)
                }
                # Track global totals
                stats["reads"] += story.get("readCount", 0)
                stats["votes"] += story.get("voteCount", 0)
                stats["comments"] += story.get("commentCount", 0)
                if story.get("qualifiedUniqueReaders"):
                    stats["engaged_readers"] += story.get("qualifiedUniqueReaders", 0)
        else:
            print(f"Stories API error: {r.status_code} {r.text}")

    except Exception as e:
        print(f"Error fetching stats: {e}")
    
    return stats


def fetch_story_parts(story_id, headers):
    """Fetch parts (chapters) with create date for key times."""
    if not story_id:
        return []
    try:
        url = f"https://www.wattpad.com/api/v3/stories/{story_id}?fields=parts(id,title,createDate)"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        parts = data.get("parts") or []
        out = []
        for p in parts:
            if not isinstance(p, dict):
                continue
            created = p.get("createDate") or p.get("create_date") or p.get("publishedDate")
            out.append({"title": p.get("title", ""), "createDate": created})
        return out
    except Exception:
        return []


def format_key_times(story_title, parts_with_dates, prev_part_count):
    """Build key times line: last chapter date, new parts since last run."""
    if not parts_with_dates:
        return None
    lines = []
    with_dates = [p for p in parts_with_dates if p.get("createDate")]
    if with_dates:
        last = with_dates[-1]
        raw = last["createDate"]
        try:
            if isinstance(raw, (int, float)):
                dt = datetime.utcfromtimestamp(raw / 1000.0 if raw > 1e10 else raw)
            else:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            lines.append(f"Last ch: {dt.strftime('%b %d')}")
        except Exception:
            pass
    curr_count = len(parts_with_dates)
    if prev_part_count is not None and curr_count > prev_part_count:
        lines.append(f"+{curr_count - prev_part_count} new pt(s)")
    if not lines and parts_with_dates:
        lines.append(f"{curr_count} pts")
    return " | ".join(lines) if lines else None


# Authenticated cookies from Google Login (temporary session)
# Authenticated cookies from Google Login (including HttpOnly tokens)
WATTPAD_COOKIES = 'remix_host_header_100=1; wp_id=47f06fdd-002e-4a88-b186-836110644eba; lang=1; _col_uuid=d7d53636-dc9c-4cc9-839b-866996001081-61f8; _gcl_au=1.1.1758562740.1773323385; _fbp=fb.1.1773323384866.993177858647880835; ff=1; dpr=2; tz=5; X-Time-Zone=America%2FWinnipeg; _pubcid=07b89579-9aea-46c1-bc34-1761bc107af1; _pubcid_cst=V0fMHQ%3D%3D; g_state={"i_l":0,"i_ll":1773324934485,"i_b":"xhMIE21fzY/QUD9sHlRt9YZbhKskNghsB+VYr8kc5Kw","i_e":{"enable_itp_optimization":0}}; token=372392295%3A2%3A1773325374%3A5EgmhrIGvFcKNvJzdaCQP83jbGReLvWKhdW8UiI8bUqGsjcIkwGr9R_dQ6rJaCYa; isStaff=1; te_session_id=1773754734717; AMP_TOKEN=%24NOT_FOUND; _gid=GA1.2.1209098643.1773754736; locale=en_US; signupFrom=story_reading; seen-series-onboarding=1; wp-web-page=true; locale=en_CA; RT=r=https%3A%2F%2Fwww.wattpad.com%2F1609583934-blue-lines-red-flags-chapter-1-caroline&ul=1773754966774&hd=1773754967207; _ga_FNDTZ0MZDQ=GS2.1.s1773754734$o3$g1$t1773754968$j32$l0$h0; _ga=GA1.1.2057394051.1773323384; cto_bundle=5cJbrF9WbmxuUW9FR2s5NVhqcWpZeVY2eEZeJTMfMkJDNUZ3QzlnYkpieSUyQmNHVDNrdzB0JTJGS3FkcmxFSldtVmRHTnNTV3VLTnVXQ1d5UGZPb1pocXJTdE1TRTRJJTJGU1loWk1IakIlMkJ0cHdYelhJb255aGtZbzNYd29ESEolMkI3NGZiV3pDZTFjT1haSHZwcU5FWG5NTG1UeUlTJTJGSG8lMkYyZElQenJuOXp3TkclMkZ2ZXZGSm8xUml5bTljb0N3dnVSRzlWbEp3UURyJTJGdkxhYnRtQ2pWdUpQNVltdVdLTm9RJTNEJTNE; cto_bidid=R1mETl9jd1BHT0NTQTNteFoybFMyWlVtaFlXMlhiNjlVcHdkWGRGYXF4V0ZjWnhJQUdkV3lpZHNpJTJCc3lpUUwzRTU2ZFdCa3BkczBoVzRGQzNHJTJCUlNCUEhlbUFUN1pzZzVBR29BU042JTJCMkglMkFOUUxJSTNWZEpEQUFlelJPNjRDbXB2VHRvNzklMkZ2ZXZGSm8xUml5bTljb0N3dnVSRzlWbEp3UURyJTJGdkxhYnRtQ2pWdUpQNVltdVdLTm9RJTNEJTNE; __qca=I0-2104904451-1773754971093'

def get_followers_list(session):
    """Fetch the current list of follower usernames."""
    followers = []
    try:
        url = f"https://www.wattpad.com/api/v3/users/{WATTPAD_USERNAME}/followers?offset=0&limit=100&fields=users(username)"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            users = data.get("users", [])
            followers = [u.get("username") for u in users if u.get("username")]
    except Exception as e:
        print(f"Error fetching followers: {e}")
    return followers

def get_recent_activity(session):
    """Fetch recent notifications and analyze timing."""
    activity = []
    hourly_activity = {} # Map of hour (0-23) to count
    try:
        url = "https://www.wattpad.com/notifications?_data=routes/_updates.notifications"
        resp = session.get(url, timeout=15, headers={'X-Remix-Redirect': 'true'})
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("notifications", {}).get("items", [])
            for item in items:
                ntype = item.get("type")
                user = item.get("from", {}).get("username")
                timestamp = item.get("createDate") # e.g. "2026-03-18T16:06:00Z"
                
                if timestamp:
                    try:
                        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                        # Adjust to local time (Assumed Central for user Emily)
                        hour = (dt.hour - 5) % 24 
                        hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                    except: pass

                if user and ntype in ["VOTE", "COMMENT"]:
                    activity.append({"user": user, "type": ntype})
    except Exception as e:
        print(f"Error fetching activity: {e}")
    
    peak_hour = None
    if hourly_activity:
        peak_hour = max(hourly_activity, key=hourly_activity.get)
        
    return activity, peak_hour

def get_reader_engagement(session, story_id):
    """Fetch unique readers and chapter retention / drop-off."""
    engagement = {"readers_today": 0, "avg_readers": 0, "retention": []}
    try:
        # 1. Activities (Unique Readers)
        act_url = f"https://www.wattpad.com/v4/stories/{story_id}/activities?interval=30"
        resp = session.get(act_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for obj in data.get("analytics", []):
                if obj.get("metric") == "readers":
                    vals = obj.get("values", {})
                    if vals:
                        # `vals` is usually a time series; we want today's readers as the
                        # most recent non-zero bucket to avoid transient 0s near send time.
                        items = list(vals.items())

                        def _parse_ts(key):
                            # Keys are often either epoch (seconds/ms) or ISO timestamps.
                            try:
                                if isinstance(key, (int, float)) or (isinstance(key, str) and key.isdigit()):
                                    num = float(key)
                                    # Heuristic: ms vs seconds.
                                    if num > 1e11:
                                        num = num / 1000.0
                                    return datetime.utcfromtimestamp(num)
                                if isinstance(key, str):
                                    return datetime.fromisoformat(key.replace("Z", "+00:00"))
                            except Exception:
                                return None
                            return None

                        parsed = [(k, v, _parse_ts(k)) for k, v in items]
                        # If at least one timestamp parses, sort by time; otherwise preserve order.
                        if any(p[2] is not None for p in parsed):
                            parsed.sort(key=lambda x: x[2] or datetime.min)
                        values_list = [int(v) for _, v, _ in parsed if v is not None]
                        if values_list:
                            readers_today = 0
                            for v in reversed(values_list):
                                if v != 0:
                                    readers_today = v
                                    break
                            engagement["readers_today"] = readers_today
                            engagement["avg_readers"] = int(sum(values_list) / len(values_list))
        
        # 2. Interactions (Retention)
        int_url = f"https://www.wattpad.com/v4/stories/{story_id}/interactions?interval=30"
        resp = session.get(int_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for obj in data.get("analytics", []):
                if obj.get("metric") == "reading_dropoff":
                    # This lists completion % for each part
                    vals = obj.get("values", [])
                    # We take the last 3-5 parts
                    engagement["retention"] = [f"{round(v * 100)}%" for v in vals[-5:]]
    except Exception as e:
        print(f"Error fetching engagement: {e}")
    return engagement

def get_wattpad_rankings(session, current):
    """
    Scrape Wattpad rankings for each story using the authenticated session.
    Parses the window.__remixContext JSON object found in the rankings page.
    """
    all_rankings = {}

    for title, stats in current.get("stories", {}).items():
        story_id = stats.get("id")
        if not story_id:
            continue

        # Remix framework direct data request
        rankings_data_url = f"https://www.wattpad.com/story/{story_id}/rankings?_data=routes%2Fstory_.$storyid.rankings"
        try:
            # We use a session with specific Remix headers
            resp = session.get(rankings_data_url, timeout=15, headers={
                'Accept': 'application/json',
                'X-Remix-Redirect': 'true'
            })
            print(f"Fetch {title} rankings: Status {resp.status_code}")
            
            story_ranks = {}
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    tag_rankings = data.get("tagRankings", [])
                    for item in tag_rankings:
                        name = item.get("name", "unknown")
                        rank = item.get("rank")
                        if rank:
                            story_ranks[name] = f"#{rank}"
                except Exception as je:
                    print(f"JSON api parse error for {title}: {je}")
            
            # Fallback to HTML scraping if API failed or returned nothing
            if not story_ranks:
                url = f"https://www.wattpad.com/story/{story_id}/rankings"
                resp = session.get(url, timeout=15)
                html = resp.text
                
                # Method 1: Parse window.__remixContext (Legacy Backup)
                match = re.search(r'window\.__remixContext\s*=\s*(\{.*?});', html)
                if match:
                    try:
                        ctx = json.loads(match.group(1))
                        loader_data = ctx.get("state", {}).get("loaderData", {})
                        for route_key, route_data in loader_data.items():
                            if isinstance(route_data, dict) and "tagRankings" in route_data:
                                for item in route_data["tagRankings"]:
                                    name = item.get("name", "unknown")
                                    rank = item.get("rank")
                                    if rank:
                                        story_ranks[name] = f"#{rank}"
                                break
                    except Exception:
                        pass

                # Method 2: Regex fallback
                if not story_ranks:
                    matches = re.findall(r"#(\d+)\s+in\s+([^<\\n]+)", html)
                    for num, cat in matches:
                        cat_clean = re.sub(r"[^a-z0-9]+", "_", cat.strip().lower()).strip("_")[:32]
                        rank_val = f"#{num}"
                        if cat_clean not in story_ranks:
                            story_ranks[cat_clean] = rank_val

            if story_ranks:
                # Normalize keys for specific requested categories
                normalized = {}
                for k, v in story_ranks.items():
                    key = k
                    if "young_adult" in k or "ya" in k: key = "young_adult"
                    elif "teen_fiction" in k: key = "teen_fiction"
                    elif "hockey" in k: key = "hockey"
                    elif "sports" in k: key = "sports"
                    normalized[key] = v
                all_rankings[title] = normalized
                
        except Exception as e:
            print(f"Error fetching rankings for {title}: {e}")

    return all_rankings


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
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        })
        for part in WATTPAD_COOKIES.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                session.cookies.set(k.strip(), v.strip())

        current = get_wattpad_stats(WATTPAD_USERNAME, session=session)
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

    # Scrape fresh rankings
    scraped_rankings = get_wattpad_rankings(session, current)
    if scraped_rankings:
        current["rankings"] = scraped_rankings
    else:
        current["rankings"] = previous.get("rankings", {})
    
    # New metrics: Retention, Engagement, Peaks
    engagement_stats = {}
    recent_activity, peak_hour = get_recent_activity(session)
    
    for title, stats in current["stories"].items():
        sid = stats.get("id")
        if sid:
            engagement_stats[title] = get_reader_engagement(session, sid)
    
    current["engagement"] = engagement_stats

    # Growth and Delta Calculations
    def get_growth_str(curr, prev):
        diff = curr - prev
        pct = (diff / prev * 100) if prev > 0 else 0
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff} | {pct:.1f}%"

    prev_reads = previous.get("reads", current["reads"])
    prev_votes = previous.get("votes", current["votes"])
    prev_engaged = previous.get("engaged_readers", current.get("engaged_readers", 0))
    prev_fols = previous.get("followers", current["followers"])

    # Historical Tracking (Keep last 7 entries)
    history = previous.get("history", [])
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "reads": current["reads"],
        "votes": current["votes"],
        "comments": current["comments"]
    })
    # Keep only the most recent 8 (to calculate 7 deltas)
    if len(history) > 8:
        history = history[-8:]
    current["history"] = history

    # Sunday Weekly Summary
    sunday_summary = ""
    is_sunday = datetime.now().weekday() == 6
    if is_sunday and len(history) >= 2:
        top_day = None
        # Gains can be negative (API corrections), so start at -inf to ensure we pick something.
        top_gain = float("-inf")
        for i in range(1, len(history)):
            prev_h = history[i-1]
            curr_h = history[i]
            gains = (curr_h["reads"] - prev_h["reads"]) + \
                    (curr_h["votes"] - prev_h["votes"]) + \
                    (curr_h["comments"] - prev_h["comments"])
            if gains > top_gain:
                top_gain = gains
                top_day = curr_h["date"]
        
        if top_day:
            sunday_summary = f"---\nWEEKLY SUMMARY:\nTOP DAY: {top_day} (+{top_gain} gains)\n"
    elif is_sunday:
        # If history is missing/too short (e.g. first run, older stats file),
        # still show a TOP DAY based on today's delta vs the last saved totals.
        today_date = datetime.now().strftime("%Y-%m-%d")
        prev_reads = previous.get("reads", current["reads"])
        prev_votes = previous.get("votes", current["votes"])
        prev_comments = previous.get("comments", current["comments"])
        gains_today = (current["reads"] - prev_reads) + (current["votes"] - prev_votes) + (current["comments"] - prev_comments)
        sunday_summary = f"---\nWEEKLY SUMMARY:\nTOP DAY: {today_date} (+{gains_today} gains)\n"

    now_str = datetime.now().strftime("%m/%d %H:%M")
    sms_text = f"Wattpad Update ({now_str}):\n"
    sms_text += f"Reads: {current['reads']} ({get_growth_str(current['reads'], prev_reads)})\n"
    sms_text += f"Votes: {current['votes']} ({get_growth_str(current['votes'], prev_votes)})\n"
    sms_text += f"Engaged: {current['engaged_readers']} ({get_growth_str(current['engaged_readers'], prev_engaged)})\n"
    sms_text += f"Followers: {current['followers']} (+{current['followers'] - prev_fols})\n"
    
    if sunday_summary:
        sms_text += sunday_summary
    
    if peak_hour is not None:
        p_str = f"{peak_hour % 12 or 12} {'PM' if peak_hour >= 12 else 'AM'}"
        sms_text += f"PEAK ACTIVITY: {p_str}\n"

    # Dedup by user and type for display
    seen_act = set()
    unique_activity = []
    for a in recent_activity:
        key = (a['user'], a['type'])
        if key not in seen_act:
            unique_activity.append(a)
            seen_act.add(key)
    
    prev_stories = previous.get("stories", {})
    prev_rankings = previous.get("rankings", {})

    # Story specific summaries
    story_summaries = []
    for title, stats in current.get("stories", {}).items():
        if stats.get("draft", False):
            continue
            
        prev_s = prev_stories.get(title, {})
        d_reads = stats["reads"] - prev_s.get("reads", stats["reads"])
        d_votes = stats["votes"] - prev_s.get("votes", stats["votes"])
        line = f"{title}: +{d_reads}R, +{d_votes}V"
        if prev_s and stats["parts"] > prev_s.get("parts", 0):
            line += " | NEW CH!"
            
        # Add rankings for this story if available
        if current.get("rankings") and title in current["rankings"]:
            ranks = current["rankings"][title]
            if isinstance(ranks, dict):
                r_lines = []
                # Select top 3 categories for brevity
                for cat, rank in list(ranks.items())[:3]:
                    curr_val = int(rank.strip('#'))
                    prev_val_str = prev_rankings.get(title, {}).get(cat, "").strip('#')
                    delta_str = ""
                    if prev_val_str:
                        prev_val = int(prev_val_str)
                        delta = prev_val - curr_val
                        if delta > 0: delta_str = f" (+{delta})"
                        elif delta < 0: delta_str = f" ({delta})"
                    r_lines.append(f"  {cat}: {rank}{delta_str}")
                if r_lines:
                    line += "\n" + "\n".join(r_lines)
        
        story_summaries.append(line)

    if story_summaries:
        sms_text += "---\nSTORY UPDATES:\n" + "\n".join(story_summaries)
        
    # Impactful Metrics Section (Voters/Commenters)
    if unique_activity:
        sms_text += "---\nRECENT ACTIVITY:\n"
        voters = [a['user'] for a in unique_activity if a['type'] == 'VOTE']
        comms = [a['user'] for a in unique_activity if a['type'] == 'COMMENT']
        if voters:
            sms_text += f"Voters: {', '.join(voters[:5])}\n"
        if comms:
            sms_text += f"Comms: {', '.join(comms[:5])}\n"

    print("Sending Notification:")
    print(sms_text)

    if "your_email" not in SENDER_EMAIL:
        send_sms(sms_text)

    current["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current, f, indent=4)


if __name__ == "__main__":
    main()
