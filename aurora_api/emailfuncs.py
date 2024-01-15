import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.contrib.sessions.backends.db import SessionStore
import os
import json
from email.mime.application import MIMEApplication



def send_email(form):
    
    # Set up the SMTP server and login
    smtp_server = "smtp.ionos.co.uk" # Replace with your SMTP server address
    smtp_port = 587  # Replace with the appropriate port number
    smtp_username = 'solomon@eazibots.com'
    smtp_password = os.environ['SMTP_PASSWORD']
    #"fntqybkejdfuwida"  
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Create a multipart message
        #send_to_user(booking_obj, server)
        send_to_practise(form, server)
        
    except Exception as e:
        print("An error occurred while sending the email:", str(e))
    finally:
        server.quit()


def send_to_practise(form, server):
    email_message = MIMEMultipart()
    email_message["From"] = 'solomon@eazibots.com'
    email_message["To"] = "biokporsolomon@yahoo.co.uk"
    email_message['Subject'] = f"Request to change record. Candidate: {form['candidate_id']}"
    
    user_name = f"{form['first_name']} {form['last_name']}"
    phone_number = form['phone_number']
    email = form['email']
    user_id = form['user_id']
    request = form['request']
    #member_no = form['member_no']
    #member_grade = form['member_grade']
    
    

    message = f"Hi,\n\nPlease see the details of this request made by {user_name} below.\nID: {user_id} below\nEmail: {email}\nPhone No: {phone_number}\nRequest: {request}."

    #f"Hi,\n\nPlease see the details of this request made by candidate ID: {candidate_id} below\nEmail: {email}\nMember No: {member_no}\nMember Grade: {member_grade}\nRequest: {request}."
    # Add the message body
    email_message.attach(MIMEText(message, "plain"))
    
    # Attach session summary as JSON
    #summary_json = json.dumps(booking_obj.summary, indent=4)
    #attachment = MIMEApplication(summary_json.encode('utf-8'))
    #attachment['Content-Disposition'] = 'attachment; filename="session_summary.json"'
    #email_message.attach(attachment)

        
    # Send the email
    server.sendmail(email_message['From'], email_message["To"], email_message.as_string())
    print(f"Email sent to {email_message['To']}")