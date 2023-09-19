from .task_utils import get_free_dates, extract_numbers, create_event, timenow
from .openaiworkers import worker_one, worker_two
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import torch
import random
from .emailcheck import is_valid_email
import time
from .booking import call_back_email, send_email
from .models import Treatments, Customer, Booking
from .emailcheck import is_valid_treatment

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
    dates = get_free_dates(session['secret'], calendar_id, booking_duration)
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
        questions = session['booking_questions']['booking questions'][category][0]
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
                    return "Please provide a valid email address!!"
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
                return response
        elif (count == len(session['question_keys']) and msg.lower() == 'no'):
            response = 'No probs'

        
        else:   
            session['summary']['booking_date'] = msg
            session['summary']['customer_name'] = session['customer_name']
            response = f"Thank you {session['summary']['client name'].split()[0]} for the info you've provided.<br/><br/> Please click the checkout button below to complete your booking and an email confirmation will be sent to you shortly."
    session['messages'].append({'role':'assistant', 'content': response})
    session.save()
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
    if prob.item() >= 0.9:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                response =  random.choices(intent['responses'])[0]
                session['messages'].append({'role':'assistant','content': response})
    elif prob.item() < 0.9:
        response = worker_one(session)
    response = response if tag in no_probe else f"{response} <br/><br/>Have I been helpful? (Y/N)"
    session['probe'] = False if tag in no_probe else True
    print(session['probe'])
    dc['response'] = response
    session.save()
    return dc
  
        

def get_response_callback(msg, session):
    session['callback'] = True
    key = ['rating', 'input', 'emai', 'input', 'output']
    value = ['Im sorry I didnt help you on this occassion. Im constantly learning and improving. Your feedback would be helpful for me.<br/><br/> First rate your experience out of 5, with 1 being the lowest.', 'What was the nature of your enquiry?', 'How was my response inadequate?']

    count = session['callbackcount']
    print(count)
    if count < len(value):
        response = value[count]
        if count > 0:
            if count == 3 and not is_valid_email(msg):
                return 'Please enter a valid email address'
            if count == 5 and not is_valid_treatment(msg, session):
                return 'Please enter a valid treatment'
            session['summary'][key[count-1]] = msg
        count += 1
        session['callbackcount'] = count
        session.save()
    else:
        session['summary'][key[count-1]] = int(msg)
        session['summary']['payment_date'] = timenow()
        session['summary']['setting'] = 'payment'
        session['callback'] = False
        session.save()
        #send email here
        response = 'Thanks a colleague of mine will be in touch shortly'
        
        #f"Thank you {session['summary']['client name'].split()[0]} for the info you've provided.<br/><br/> Please click the checkout button below to complete your payment and an email confirmation will be sent to you shortly."
        
    return response

        
