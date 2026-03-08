# Daily Wattpad SMS Notifier

This repo sends a **daily SMS** to your phone at **7:00 PM Central** with your Wattpad stats and **today’s ranks**. It uses **Email-to-SMS** (carrier gateway), so no extra app—just real SMS.

## How it works

- **GitHub Actions** runs the script every day at 7 PM Central.
- The script fetches your Wattpad stats (reads, votes, comments, followers) from the Wattpad API.
- It sends an email to your carrier’s **Email-to-SMS gateway** (e.g. `number@msg.telus.com`); your carrier turns that into an SMS.

## Setup (one-time)

### 1. Add repository secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret.** Add:

| Secret              | Example                    | Description                          |
|---------------------|----------------------------|--------------------------------------|
| `PHONE_EMAIL`       | `2043830396@msg.telus.com` | Your phone number @ carrier gateway  |
| `SENDER_EMAIL`      | `you@gmail.com`           | Gmail (or other) address that sends  |
| `SENDER_PASSWORD`   | (16-char app password)     | Gmail [App password](https://myaccount.google.com/apppasswords) |
| `WATTPAD_USERNAME`  | `wlwsports`               | Optional; default is wlwsports       |

### 2. Carrier gateways (Canada)

- **Telus:** `number@msg.telus.com`
- **Rogers:** `number@pcs.rogers.com`
- **Bell/MTS:** `number@text.mts.net` or `number@txt.bell.ca`
- **Virgin:** `number@vmobile.ca`
- **Fido:** `number@fido.ca`
- **Koodo:** `number@msg.koodomobile.com`

### 3. Deploy

Push this repo (or copy these files into [emilyfehr99/wattpad](https://github.com/emilyfehr99/wattpad)). The workflow **Wattpad Daily SMS** will run on schedule. You can also run it manually: **Actions → Wattpad Daily SMS → Run workflow.**

## Today’s ranks in the SMS

The message includes a **“TODAY’S RANKS”** section when rankings are stored in `wattpad_stats.json` under a `rankings` key. To get ranks into the SMS:

1. **Option A – Manual:** Edit `wattpad_stats.json` and add a `rankings` object, e.g.:

```json
"rankings": {
  "Blue Lines, Red Flags": {
    "young_adult": "#397",
    "sports": "#110",
    "romance": "#572",
    "teen_fiction": "#249",
    "hockey": "#12"
  }
}
```

2. **Option B – Script:** Run a separate script or cron that updates `wattpad_stats.json` with rankings (e.g. from Wattpad’s site or a scraper), then commit and push so the daily run uses the latest ranks.

After the daily job runs, it commits updated `wattpad_stats.json` (including any rankings) so the next run has the latest data.

## Files

- `wattpad_notifier.py` – Fetches Wattpad API, builds SMS text (with ranks if present), sends via Email-to-SMS.
- `wattpad_stats.json` – Persisted stats (and optional `rankings`); updated and committed by the workflow.
- `.github/workflows/daily.yml` – Runs at 7 PM Central, uses the secrets above.

## Local test

```bash
cd /path/to/wattpad
export PHONE_EMAIL="YOUR_NUMBER@msg.telus.com"
export SENDER_EMAIL="you@gmail.com"
export SENDER_PASSWORD="your_app_password"
python wattpad_notifier.py
```

You’ll get one SMS immediately and `wattpad_stats.json` will be updated.
