# Daily Wattpad SMS Notifier

This Python script retrieves your daily Wattpad statistics—specifically total reads and total votes—and calculates the number of **readers you gained that day**. It then sends a short SMS notification directly to your phone for free.

## How it works (Free SMS)
The script uses **Email-to-SMS Gateway** routing. By sending an email to a specific carrier gateway address (e.g., `1234567890@vtext.com` for Verizon), your mobile provider automatically converts the email into an SMS text message directly to your phone at no cost.

## Setup Instructions

### 1. Configure the Script
Open `/Users/emilyfehr8/CascadeProjects/wattpad_notifier.py` and modify the fields at the top:

```python
PHONE_EMAIL = "2043830396@yourcarrier.ca"  # Replace yourcarrier.ca with your carrier below!

SENDER_EMAIL = "your_email@gmail.com"  # Your sending email
SENDER_PASSWORD = "your_app_password"  # Your App Password
```

**Common Canadian Carrier Gateways:**
- **Bell or MTS:** `2043830396@text.mts.net` OR `2043830396@txt.bell.ca`
- **Rogers:** `2043830396@pcs.rogers.com`
- **Telus:** `2043830396@msg.telus.com`
- **Virgin Mobile:** `2043830396@vmobile.ca`
- **Fido:** `2043830396@fido.ca`
- **Koodo:** `2043830396@msg.koodomobile.com`

*Note: For `SENDER_PASSWORD`, if you are using Gmail, you cannot use your standard password. You must go to your Google Account > Security > 2-Step Verification > **App passwords** to generate a 16-character app password to use here.*

### 2. Required Libraries
Ensure you have the requests library installed:
```bash
pip install requests
```

### 3. Automating Daily Texts (Mac OS)
To run this automatically every single day, you can use the built-in Mac OS `cron` job scheduler.

1. Open your terminal.
2. Type `crontab -e` and press Enter.
3. Press `i` to enter insert mode.
4. Paste the following line to run the script every day at 7:00 PM (19:00):
```bash
0 19 * * * /usr/bin/python3 /Users/emilyfehr8/CascadeProjects/wattpad_notifier.py >> /tmp/wattpad_cron.log 2>&1
```
5. Press `Esc`, then type `:wq`, and press Enter to save and exit.

You will now receive a text every morning with your daily Wattpad stats!
