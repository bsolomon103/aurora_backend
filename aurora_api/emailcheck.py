import re
import smtplib

def check_email_deliverability(sender_email, recipient_email, smtp_server, smtp_port, username, password):
    try:
        # Establish a connection to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption for secure communication

        # Log in to the SMTP server
        server.login(username, password)

        # Send a test email
        server.sendmail(sender_email, recipient_email, "TEST MESSAGE")

        # Close the connection
        server.quit()

        #print("Email deliverability check successful.")
        return True
    except smtplib.SMTPException as e:
        #print("Email deliverability check failed. Reason:", str(e))
        return False


def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email) is not None:
        return False
    else:
        return True



def is_valid_treatment(msg, session):
    treatments = session['mappings']['booking categories']
    if msg.lower() in treatments:
        return True
    return False