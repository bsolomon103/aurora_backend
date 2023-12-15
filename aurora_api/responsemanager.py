from .task_utils import get_free_dates, extract_numbers, create_event, timenow
from .openaiworkers import worker_one, worker_two, worker_three
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
#from .chain import build_chain
from .langmodels import chain

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


        
def download_s3_folder(s3_folder, local_dir=None):
    """
    Download the contents of a folder directory
    Args:
        bucket_name: the name of the s3 bucket
        s3_folder: the folder path in the s3 bucket
        local_dir: a relative or absolute directory path in the local file system
    """
    s3 = boto3.resource('s3')
    bucket_name = os.environ['AWS_STORAGE_BUCKET_NAME']
    bucket = s3.Bucket(bucket_name)
    # Extract the folder name from the S3 folder path
    folder_name = os.path.basename(s3_folder.rstrip('/'))
    
    for obj in bucket.objects.filter(Prefix=s3_folder):
        print(obj.key)
        target = obj.key if local_dir is None \
            else os.path.join(local_dir, folder_name, os.path.relpath(obj.key, s3_folder))
        
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        if obj.key[-1] == '/':
            continue
        bucket.download_file(obj.key, target)
        
        

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
    print('Getting Dates')
    treatment_required = session['booking_category']
    practise_name = session['customer_name']
    practise_obj = Customer.objects.get(name=practise_name)
    treatment_obj = Treatments.objects.get(customer_name=practise_obj, treatment=treatment_required.title())
    booking_duration = treatment_obj.booking_duration 
    calendar_id = treatment_obj.calendar_id
    secret = get_or_download_secret('Google.json')
    dates = get_free_dates(secret, calendar_id, booking_duration)
    response = dates
    session.save()
    return response

def get_response_booking(msg, session):
    con_summ = ''
    if 'questions' not in session:
        category = worker_two(session, session['mappings'])
        session['booking_category'] = category
        session['summary']['treatment category'] = category
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
    current_messages = session['messages']
    current_messages = current_messages + f"user: {msg}\n"
    session['messages'] = current_messages
    #print(session['messages'])
    session.save()
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
    session['intent'] = tag
    print(tag, prob.item())
    if session['get_team']:
        tag = worker_three(session)
        session['intent'] = tag
        for intent in intents['intents']: 
            if tag == intent['tag']:
                response =  random.choices(intent['responses'])[0]
                session['messages'].append({'role':'assistant','content': response})
    
    else:
        data = chain(session, msg)
        return data
        '''
        for chunk in build_chain(session, msg):
            yield chunk
        '''

  
        
def get_response_feedback(msg, session):
    session['feedback'] = True
    '''
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
    response = {"response": {'text': response, "buttons" : None, 'probe': True}}
    session['count'] = count
    '''
    
    response = 'So I can direct you to the right team, could you tell me what the topic of your question is?'
    session['get_team'] = True
    session.save()
    return {'response': {'text': response, 'probe': 'False'}}