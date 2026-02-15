from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from logger_utils import create_logger
from credential import EmailCredential

logger = create_logger("email_manager")


def send_email(body, subject,receiver_email, is_html=True):
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = EmailCredential.get_email_address()
    password = EmailCredential.get_email_password()


    # Set up the MIME
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    if is_html:
        message.attach(MIMEText(body, "html"))
    else:
        message.attach(MIMEText(body, "plain"))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())
        logger.info(f"Email sent successfully to {receiver_email}!")

    except Exception as e:
        logger.error(f"Error while sending email: {e}")

    finally:
        # Close the connection to the SMTP server
        server.quit()