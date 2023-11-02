from .task_utils import get_free_dates, extract_numbers, create_event, timenow
from .openaiworkers import worker_one, worker_two
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
from .celeryfuncs import cache_chat_message
import torch
import random
import boto3
import os
from .emailcheck import is_valid_email
import time
from django.conf import settings
from .booking import call_back_email, send_email
from .models import Treatments, Customer, Booking
from .emailcheck import is_valid_treatment
from .questions import questionsdc

def download_file_from_s3(local_directory, file_reference):
    s3 = boto3.client('s3')
    bucket_name = os.environ['AWS_STORAGE_BUCKET_NAME']
    directory = os.path.join(settings.BASE_DIR, 'media')  # Local file path where you want to save the downloaded file
    file_path = os.path.join(directory, local_directory, file_reference)
    print(file_path)
    
    try:
        s3.download_file(bucket_name, file_reference, file_path)
        return file_path
    except Exception as e:
        # Handle exceptions (e.g., file not found in S3, permissions issues, etc.)
        print(f"Error: {e}")
        return None

def get_or_download_secret(secret_file):
     # Specify the local file path where you expect the training file to be
    local_file = os.path.join(settings.BASE_DIR, 'media', 'secrets_file', secret_file)

    # Check if the local file exists
    if os.path.exists(local_file):
        return local_file
     
    else:
        # The local file doesn't exist, download it from S3
        local_trainingfile = download_file_from_s3('secrets_file', secret_file)
        if local_trainingfile:
            return local_file

def start_assessment(msg, session):
    session['booking_on'] = True
    session.save()
    
def get_response_dates(msg, session):
    print('')
    treatment_required = session['booking_category']
    practise_name = session['customer_name']
    practise_obj = Customer.objects.get(name=practise_name)
    treatment_obj = Treatments.objects.get(customer_name=practise_obj, treatment=treatment_required.title())
    booking_duration = treatment_obj.booking_duration 
    calendar_id = treatment_obj.calendar_id
    secret = get_or_download_secret('Google.json')
    print(secret)
    dates = get_free_dates(secret, calendar_id, booking_duration)
    response = dates
    session.save()
    return response

def get_response_booking(msg, session):
    con_summ = ''
    if 'questions' not in session:
        category = worker_two(session, session['mappings'])
        #print(category)
        session['booking_category'] = category
        session['summary']['treatment category'] = category
        #questions = session['booking_questions']['booking questions'][category][0] # this is where the change can be made !!!
        questions = questionsdc['booking questions'][category][0]
        session['questions'] = questions
        session['question_keys'] += list(questions.keys())
        count = session['count']
        question_key = session['question_keys'][count]
        response = session['questions'][question_key]
        count += 1
        session['count'] = count
    else:
        count = session['count']
        if count < len(session['question_keys']):
            question_key = session['question_keys'][count]
            response = session['questions'][question_key]
            prev_key = session['question_keys'][count-1]
            session['summary'][prev_key] = msg

            #move into a different file with validations across the key i.e. patient status 
            if question_key.lower() == 'email':
                first_name = session['summary']['client name'].split()[0]
                response = f"Hi {first_name}, nice to meet you. {response}"
            if prev_key.lower() == 'quantity desired':
                session['summary'][prev_key] = str(extract_numbers(msg))
            if prev_key.lower() == 'email':
                if not (is_valid_email(msg)):
                    response =  "Please provide a valid email address!!"
                    cache_chat_message(session['session_key'], msg, response, session['rating'], session['intent'])
                    return response
            elif (session['summary']['treatment category'].lower() not in ('generic toothache') and count == len(session['question_keys']) - 1):
                response = f"Thanks {session['summary']['client name'].split()[0]},<br/><br/>{response}"
            count += 1
            session['count'] = count
            
        elif (count == len(session['question_keys']) and msg.lower() == 'yes'):
            setting = session['treatment_init'][session['booking_category']]
            if setting == 'in-person':
                session['summary'][session['question_keys'][count-1]] = msg
                response = get_response_dates(msg, session)
                session.save()
                #cache_chat_message(session['session_key'], msg, response, session['rating'], session['intent'])
                return response
        elif (count == len(session['question_keys']) and msg.lower() == 'no'):
            response = 'No probs'
        else:   
            session['summary']['booking_date'] = msg
            session['summary']['customer_name'] = session['customer_name']
            response = f"Thank you {session['summary']['client name'].split()[0]} for the info you've provided.<br/><br/> Please click the checkout button below to complete your booking and an email confirmation will be sent to you shortly."
    session['messages'].append({'role':'assistant', 'content': response})
    session.save()
    cache_chat_message(session['session_key'], msg, response, session['rating'], session['intent'])
    return response

def get_response_aurora(msg, model, all_words, tags, session, device):
    session['messages'].append({'role':'user', 'content': msg})
    intents = session['intents']
    no_probe = session['closing']
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)
    output = model(X)
    _,predicted = torch.max(output,dim=1)
    tag = tags[predicted.item()]
    probs = torch.softmax(output,dim=1)
    prob = probs[0][predicted.item()]
    dc = {}
    dc['input_tag'] = tag
    session['intent'] = tag
    print(tag, prob.item())
    if prob.item() >= 0.9:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                response =  random.choices(intent['responses'])[0]
                session['messages'].append({'role':'assistant','content': response})
                response = response if tag in no_probe else f"{response} <br/><br/><div style='display:flex; justify-content:center;'>Have I been helpful? (Y/N)</div>"

    elif prob.item() < 0.9:
        #response = worker_one(session)
        response = get_response_callback(msg, session)
    session['probe'] = False if tag in no_probe else True
    #print(session['probe'])
    dc['response'] = response
    session.save()
    cache_chat_message(session['session_key'], msg, response, None, session['intent'])
    return dc
  
        

def get_response_callback(msg, session):
    session['callback'] = True
    session['rating'] = 'No'
    key = ['input', 'output', 'rating']
    value = ['Im sorry I cant answer your query with a high degree of confidence yet, i am constanly learning and improving. Your feedback will help me learn faster.<br/><br/> Firstly, what was the nature of your request?',
            'How was my response inadequate?', 'Rate your experience out of 5, with 1 - poor and 5 - good']
    
    count = session['count']
    if count < len(value):
        response = value[count]
        cache_chat_message(session['session_key'], msg, response, session['rating'], session['intent'])
        count += 1
    else:
        session['callback'] = False
        response = 'Thanks for your valuable feedback. This information will be used to make me better.'
        cache_chat_message(session['session_key'], msg, response,session['rating'],session['intent'])
    session['count'] = count
    session.save()
    return response