from .task_utils import create_event
from .models import Booking
from django.db.models import Q
from aurora_api.models import Customer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.contrib.sessions.backends.db import SessionStore
import os

def update_create_event(username, useremail):
    print(username, username)
    booking_obj = Booking.objects.filter((Q(patient_name__icontains=username) & Q(booking_status='unpaid')) |
    (Q(patient_email__contains=useremail) & Q(booking_status='unpaid')))
    booking_obj = list(booking_obj)
    booking_obj = booking_obj[-1]
    booking_obj.booking_status = 'paid'
    booking_obj.save()
    event_date = booking_obj.booking_date
    calendar_id = booking_obj.calendar_id
    duration = booking_obj.booking_duration
    
    #Function to create calendar event
    create_event(event_date, calendar_id, duration)
    #Function to send confirmation emailss
    send_email(booking_obj)
    

    
def update_failed_event(username, useremail):
    print(username, username)
    booking_obj = Booking.objects.filter((Q(user_name__icontains=username) & Q(booking_status='unpaid')) |
    (Q(email__contains=useremail) & Q(booking_status='unpaid')))
    booking_obj = list(booking_obj)
    obj = booking_obj[-1]
    obj.booking_status = 'failed'
    obj.save()



def send_email(booking_obj):
    # Set up the SMTP server and login
    smtp_server = "smtp.mail.yahoo.com" # Replace with your SMTP server address
    smtp_port = 587  # Replace with the appropriate port number
    smtp_username = 'biokporsolomon@yahoo.co.uk'
    smtp_password = os.environ['SMTP_PASSWORD']
    #"fntqybkejdfuwida"  
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Create a multipart message
        send_to_user(booking_obj, server)
        send_to_practise(booking_obj, server)
        
    except Exception as e:
        print("An error occurred while sending the email:", str(e))
    finally:
        server.quit()

def send_to_user(booking_obj, server):
    email_message = MIMEMultipart()
    email_message["From"] = 'biokporsolomon@yahoo.co.uk'
    email_message["To"] = booking_obj.patient_email
    email_message["Subject"] = f"{booking_obj.practise_name} appointment confirmation"
    date = booking_obj.booking_date.split('T')[0]
    time = booking_obj.booking_date.split('T')[1].split('+')[0]
    message = f"Hi {booking_obj.patient_name.split()[0]},\n\nThis is a confirmation email, see below for full details.\n\nTreatment: {booking_obj.treatment}\nPractise Name: {booking_obj.practise_name}\nBooking Date: {date}\nBooking Time: {time}\n\nIf you have any questions feel free to reach out to {booking_obj.practise_name}\nEmail: {booking_obj.practise_email}\nPhone: {booking_obj.practise_phone}\nKind Regards,\nEaziBots"
    # Add the message body
    email_message.attach(MIMEText(message, "plain"))
        
    # Send the email
    server.sendmail('biokporsolomon@yahoo.co.uk', email_message['To'], email_message.as_string())
    print(f"Email sent to {email_message['To']}")
    
def send_to_practise(booking_obj, server):
    email_message = MIMEMultipart()
    email_message["From"] = 'biokporsolomon@yahoo.co.uk'
    email_message["To"] = booking_obj.practise_email
    email_message["Subject"] = f"EaziBots Confirmation: Scheduled Appointment with {booking_obj.patient_name} for {booking_obj.treatment}"
    date = booking_obj.booking_date.split('T')[0]
    time = booking_obj.booking_date.split('T')[1].split('+')[0]
    total_summary = ''
    for k, v in dict(booking_obj.summary).items():
        if k.lower() not in ('sales question','phone','email','client name','treatment category','booking_date','customer_name'):
            ind_summary = k + ' : ' + v + '\n'
            total_summary += ind_summary
        #print(total_summary)
            
        #print(k,v)
    message = f"Hi {booking_obj.practise_name},\n\nThis is a confirmation email, see below for full details.\n\nTreatment: {booking_obj.treatment}\nPatient Name: {booking_obj.patient_name}\nOrder ID: {booking_obj.id}\nBooking Date: {date}\nBooking Time: {time}\nEmail: {booking_obj.patient_email}\nPhone Number: {booking_obj.patient_phone}\n{total_summary}.\nIf you have any questions regarding this booking reach out to us on orders@eazibots.com and quote the order id.\n\nKind regards,\nEaziBots"
    # Add the message body
    email_message.attach(MIMEText(message, "plain"))
        
    # Send the email
    server.sendmail('biokporsolomon@yahoo.co.uk', email_message["To"], email_message.as_string())
    print(f"Email sent to {email_message['To']}")
    


def call_back_email(session):
    # Set up the SMTP server and login
    smtp_server = "smtp.mail.yahoo.com" # Replace with your SMTP server address
    smtp_port = 587  # Replace with the appropriate port number
    smtp_username = 'biokporsolomon@yahoo.co.uk'
    smtp_password = os.environ['SMTP_PASSWORD']
    #"fntqybkejdfuwida"  
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        patient_name = session['summary']['Whats your full name ?']
        number = session['summary']['Whats your phone number ?']
        email = session['summary']['Whats your email address ?']
        dob = session['summary']['Date of Birth']
        interest = session['summary']['What treatment(s) are you interested in ?']
        enquiry = session['summary']['Describe your enquiry in your own words.']
        preference = session['summary']['What time of day should we call ?']
        
        email_message = MIMEMultipart()
        email_message["From"] = 'biokporsolomon@yahoo.co.uk'
        email_message["To"] = session['email']
        email_message["Subject"] = f"EaziBots Call Back Request: {patient_name}"
            
        # Create a multipart message
        message = f"Hi {session['customer_name']},\n\nThis is confirmation of a call back request, see details below:\nPatient Name: {patient_name}\nPhone Number: {number}\nEmail: {email}\nDate of Birth: {dob}\nInterested In: {interest}\nEnquiry: {enquiry}\nPreferred Contact Time: {preference}\n.\nIf you have any questions regarding this booking reach out to us on orders@eazibots.com and quote this id {session['session_key']}\n\nKind regards,\nEaziBots"
        email_message.attach(MIMEText(message, "plain"))
        
        # Send the email
        server.sendmail('biokporsolomon@yahoo.co.uk', email_message["To"], email_message.as_string())
        print(f"Email sent to {email_message['To']}")
        
        
    except Exception as e:
        print("An error occurred while sending the email:", str(e))
    finally:
        server.quit()
    return

