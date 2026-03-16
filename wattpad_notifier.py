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
            if not isinstance(story, dict):
                continue
            title = story.get('title', 'Unknown')
            story_id = story.get('id')
            story_url = story.get('url')  # e.g. "/story/407902208-blue-lines-red-flags"
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
                "url": story_url,
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
WATTPAD_COOKIES = 'remix_host_header_100=1; wp_id=47f06fdd-002e-4a88-b186-836110644eba; lang=1; _col_uuid=d7d53636-dc9c-4cc9-839b-866996001081-61f8; token=372392295%3A2%3A1773325374%3A5EgmhrIGvFcKNvJzdaCQP83jbGReLvWKhdW8UiI8bUqGsjcIkwGr9R_dQ6rJaCYa; _gcl_au=1.1.1758562740.1773323385; _fbp=fb.1.1773323384866.993177858647880835; adMetrics=0; wp-web-auth-cache-bust=0; _pbeb_=1; _pbbeta25_=1; ff=1; dpr=2; tz=5; X-Time-Zone=America%2FWinnipeg; _pubcid=07b89579-9aea-46c1-bc34-1761bc107af1; _pubcid_cst=V0fMHQ%3D%3D; cto_bundle=cp0urV9WbmxuUW9FR2s5NVhqcWpZeVY2eEZ5RTVIdXE2ZTh5YlB3aWFaa29OR05sOXhNd3JHcWFGSUEyWG4wTiUyQmIlMkI4dDIxVmM0dHN3c2xlZWtPckNMem1jZUlCNjkxVm5LeHRRV0JBTXRDNTRhZ28lMkYyZElQenJuOXp3TkclMkZ2ZXZGSm8xUml5bTljb0N3dnVSRzlWbEp3UURyJTJGdkxhYnRtQ2pWdUpQNVltdVdLTm9RJTNEJTNE; cto_bidid=UzPRml9jd1BHT0NTQTNteFoybFMyWlVtaFlXMlhiNjlVcHdkWGRGYXF4V0ZjWnhJQUdkV3lpZHNpJTJCc3lpUUwzRTU2ZFc5dmFNaEwzdGRSRnh0Mmw0WFE4TFNWYzdBcGxnOURoT1Vnd2x6aFhzcFN4TklHZXVzeXFyWmJSN0FlTWFHNExsdU9vWWVDUSUyRnQ0QUY3YXpMWWVEQ2JRJTNEJTNE; g_state={"i_l":0,"i_ll":1773324934485,"i_b":"xhMIE21fzY/QUD9sHlRt9YZbhKskNghsB+VYr8kc5Kw","i_e":{"enable_itp_optimization":0}}; wp-web-page=true; locale=en_CA; te_session_id=1773664654713; AMP_TOKEN=%24NOT_FOUND; _ga=GA1.2.2057394051.1773323384; _gid=GA1.2.1695821674.1773664656; _ga_FNDTZ0MZDQ=GS2.1.s1773664655$o2$g1$t1773664665$j50$l0$h0'

def get_wattpad_rankings(current):
    """
    Scrape Wattpad rankings for each story using the authenticated session.
    Parses the window.__remixContext JSON object found in the rankings page.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
    })
    
    # Load cookies
    for part in WATTPAD_COOKIES.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            session.cookies.set(k.strip(), v.strip())

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

    # Scrape fresh rankings; if that fails, fall back to last saved rankings
    scraped_rankings = get_wattpad_rankings(current)
    if scraped_rankings:
        current["rankings"] = scraped_rankings
    else:
        current["rankings"] = previous.get("rankings", {})
    prev_stories = previous.get("stories", {})

    # Key times: last chapter date, new parts since last run
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    key_times_lines = []
    for title, stats in current["stories"].items():
        parts_with_dates = fetch_story_parts(stats.get("id"), headers)
        prev_part_count = prev_stories.get(title, {}).get("parts") if title in prev_stories else None
        line = format_key_times(title, parts_with_dates, prev_part_count)
        if line:
            key_times_lines.append(f"{title}: {line}")

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

    if key_times_lines:
        sms_text += "---\nKEY TIMES:\n"
        sms_text += "\n".join(key_times_lines) + "\n"

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

    print("Sending Notification:")
    print(sms_text)

    if "your_email" not in SENDER_EMAIL:
        send_sms(sms_text)

    current["timestamp"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(current, f, indent=4)


if __name__ == "__main__":
    main()
