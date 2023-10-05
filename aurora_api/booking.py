from .task_utils import create_event
from .models import Booking
from django.db.models import Q
from aurora_api.models import Customer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.contrib.sessions.backends.db import SessionStore
import os
import json
from email.mime.application import MIMEApplication

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
    patient_name = booking_obj.patient_name
    treatment = booking_obj.treatment
    setting = booking_obj.setting
    duration = booking_obj.booking_duration if event_date != 'payment' else 0
    

    #Function to create calendar event
    if event_date != 'payment':
        create_event(patient_name, treatment, event_date, booking_obj.setting, calendar_id, duration)
    print('skeeyee')
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
        send_to_user(booking_obj, server)
        send_to_practise(booking_obj, server)
        
    except Exception as e:
        print("An error occurred while sending the email:", str(e))
    finally:
        server.quit()

def send_to_user(booking_obj, server):
    email_message = MIMEMultipart()
    email_message["From"] = 'solomon@eazibots.com'
    email_message["To"] = booking_obj.patient_email
    if booking_obj.setting.lower() == 'payment':
        prefix = "Payment confirmation for "
        datevar = "Payment Date"
        timevar = "Payment Time"
    elif booking_obj.setting.lower() == 'in-person':
        prefix = 'In person appointment confirmation for '
        datevar = "Appointment Date"
        timevar = "Appointment Time"
    else:
        prefix = 'Appointment confirmation for '
        datevar = "Appointment Date"
        timevar = "Appointment Time"
        
    email_message["Subject"] = f"{prefix}{booking_obj.treatment} with {booking_obj.practise_name}"
    date = booking_obj.booking_date.split('T')[0]
    time = booking_obj.booking_date.split('T')[1].split('+')[0]
    
    message = f"Hi {booking_obj.patient_name.split()[0]},\n\nThis is a confirmation email, see below for full details.\n\nService: {booking_obj.treatment}\nOrganisation Name: {booking_obj.practise_name}\n{datevar} {date}\n{timevar} {time}\nAmount Paid: {booking_obj.price}\n\nIf you have any questions feel free to reach out to {booking_obj.practise_name}\nEmail: {booking_obj.practise_email}\nPhone: {booking_obj.practise_phone}\nKind Regards,\nEaziBots"
    # Add the message body
    email_message.attach(MIMEText(message, "plain"))
    

        
    # Send the email
    server.sendmail(email_message['From'], email_message['To'], email_message.as_string())
    print(f"Email sent to {email_message['To']}")
    
def send_to_practise(booking_obj, server):
    email_message = MIMEMultipart()
    email_message["From"] = 'solomon@eazibots.com'
    email_message["To"] = booking_obj.practise_email
    if booking_obj.setting.lower() == 'payment':
        prefix = "Payment confirmation for "
        datevar = "Payment Date"
        timevar = "Payment Time"
    elif booking_obj.setting.lower() == 'in-person':
        prefix = 'In person appointment confirmation for '
        datevar = "Appointment Date"
        timevar = "Appointment Time"
    else:
        prefix = 'Appointment confirmation for '
        datevar = "Appointment Date"
        timevar = "Appointment Time"
    email_message["Subject"] = f"{prefix}{booking_obj.patient_name} for {booking_obj.treatment}"
    date = booking_obj.booking_date.split('T')[0]
    time = booking_obj.booking_date.split('T')[1].split('+')[0]

    message = f"Hi {booking_obj.practise_name},\n\nThis is a confirmation email, see below for full details.\n\nService: {booking_obj.treatment}\nBooking Name: {booking_obj.patient_name}\nOrder ID: {booking_obj.id}\n{datevar} {date}\n{timevar} {time}\nEmail: {booking_obj.patient_email}\nPhone Number: {booking_obj.patient_phone}\nAmount Paid: {booking_obj.price}.\nIf you have any questions regarding this booking reach out to us on solomon@eazibots.com and quote the order id.\n\nKind regards,\nEaziBots"
    # Add the message body
    email_message.attach(MIMEText(message, "plain"))
    
    # Attach session summary as JSON
    summary_json = json.dumps(booking_obj.summary, indent=4)
    attachment = MIMEApplication(summary_json.encode('utf-8'))
    attachment['Content-Disposition'] = 'attachment; filename="session_summary.json"'
    email_message.attach(attachment)

        
    # Send the email
    server.sendmail(email_message['From'], email_message["To"], email_message.as_string())
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
        patient_name = session['summary']['client name']
        number = session['summary']['phone']
        email = session['summary']['email']
        #dob = session['summary']['date of birth']
        interest = session['summary']['treatment category']
        enquiry = 'test'
        preference = 'test'
        
        email_message = MIMEMultipart()
        email_message["From"] = 'biokporsolomon@yahoo.co.uk'
        email_message["To"] = session['email']
        email_message["Subject"] = f"EaziBots Call Back Request: {patient_name}"
            
        # Create a multipart message
        message = f"Hi {session['customer_name']},\n\nThis is confirmation of a call back request, see details below:\nPatient Name: {patient_name}\nPhone Number: {number}\nEmail: {email}.\nIf you have any questions regarding this booking reach out to us on orders@eazibots.com and quote this id {session['session_key']}\n\nKind regards,\nEaziBots"
        email_message.attach(MIMEText(message, "plain"))
        
        # Attach session summary as JSON
        summary_json = json.dumps(session['summary'], indent=4)
        attachment = MIMEApplication(summary_json.encode('utf-8'))
        attachment['Content-Disposition'] = 'attachment; filename="session_summary.json"'
        email_message.attach(attachment)

        
        # Send the email
        server.sendmail('biokporsolomon@yahoo.co.uk', email_message["To"], email_message.as_string())
        print(f"Email sent to {email_message['To']}")
        
        
    except Exception as e:
        print("An error occurred while sending the email:", str(e))
    finally:
        server.quit()
    return

