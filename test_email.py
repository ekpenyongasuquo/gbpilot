import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

SENDER_EMAIL = os.getenv("OUTREACH_EMAIL")
SENDER_PASSWORD = os.getenv("OUTREACH_PASSWORD")

def test_email():
    recipient = SENDER_EMAIL  # sending to yourself first

    subject = "GBPilot Test — Your Google listing is losing $3,500/month"

    body = """
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px;">

<p>Hi Smith Family Dental team,</p>

<p>I ran a quick AI audit on your Google Business Profile and found something worth flagging.</p>

<p style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px;">
  <strong>Your listing scored 45/100 on local visibility</strong> — which means 
  you're likely missing out on an estimated <strong>$3,500 in revenue every month</strong> 
  from customers searching Google for businesses like yours.
</p>

<p>The biggest issue we found:</p>
<p style="background: #f8fafc; padding: 12px; border-radius: 4px;">
  ⚠️ Extremely low number of reviews (only 4) significantly impacts trust and visibility.
</p>

<p>The top fix:</p>
<p style="background: #f0fdf4; padding: 12px; border-radius: 4px;">
  ✅ Implement a proactive review generation strategy targeting satisfied customers immediately after service.
</p>

<p>I've attached your full AI audit report — it breaks down exactly what's hurting 
your ranking and what fixes would have the biggest impact.</p>

<p>
  <a href="https://gbpilot.onrender.com" 
     style="background: #1e40af; color: white; padding: 12px 24px; 
            border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
    See Your Full Audit Report →
  </a>
</p>

<p>If you want GBPilot to handle all of this automatically — posts, fixes, monitoring — 
it's <strong>$79/month per location</strong>, and the first 7 days are free.</p>

<p>Best,<br>
<strong>Ekpenyong Mfon</strong><br>
GBPilot — AI-Powered Google Business Profile Management<br>
https://gbpilot.onrender.com
</p>

</body>
</html>
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

        print(f"✅ Test email sent successfully to {recipient}")
        print("Check your Gmail inbox now.")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")


if __name__ == "__main__":
    test_email()