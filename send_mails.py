import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = ""
EMAIL_PASSWORD = ""  

recipients = [""] # List of recipient email addresses

subject = "Early Access to Tross — Build Faster, Debug Smarter"

html_body = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
  <p>Let’s cut to the chase — <b>your dev team is brilliant</b>, but they’re spending way too much time wrestling with bugs and executing redundant tasks instead of building your next breakthrough.</p>

  <h3>🚀 How Tross Helps Your Team</h3>
  <p><b>Tross</b> tries and enables your developers to:</p>
  <ul>
    <li>Execute tasks in the cloud-based IDEs on simple context descriptions</li>
    <li>Improve code across multiple files</li>
    <li>Try and resolve bugs remotely without opening local IDEs</li>
  </ul>
  <p>Our <b>multi-agent architecture</b> ensures the entire process is feasible — exactly what growing startups need.</p>

  <h3>🎟️ Get Early Access</h3>
  <p>We're offering select startups like you <b>exclusive early access</b> to Tross. To secure your spot:</p>
  <ol>
    <li>Visit <a href="https://website.link/tross-early-access">website.link/tross-early-access</a></li>
    <li>Create your account and you will get an early access token in your mail</li>
    <li>Start transforming your development workflow immediately</li>
  </ol>

  <br>
  <p>Best regards,<br><b>Tross by BytQuest</b><br>Email: <a href="mailto:bytquest@gmail.com">bytquest@gmail.com</a></p>
</body>
</html>
"""

def send_email():
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for recipient in recipients:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))
        server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        print(f"✅ Email sent to {recipient}")

    server.quit()

if __name__ == "__main__":
    send_email()
