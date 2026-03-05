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

### 3. Deploy to GitHub (Free Automation)
To run this automatically every single day at 7:00 PM without needing your Mac to be on:

1. Go to [GitHub.com](https://github.com/) and create a new repository named `wattpad` (Private or Public).
2. Open your Mac Terminal and push this folder to your new repository:
```bash
cd /Users/emilyfehr8/CascadeProjects/wattpad_notifier
git remote add origin https://github.com/YOUR_USERNAME/wattpad.git
git branch -M main
git push -u origin main
```
3. GitHub Actions will now automatically run the script every day at your scheduled time (7:00 PM CST). You will start receiving texts immediately!
