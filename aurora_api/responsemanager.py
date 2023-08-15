from .task_utils import get_free_dates, extract_numbers
from .openaiworkers import worker_one, worker_two, worker_three, worker_four
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import torch
import random
from .emailcheck import is_valid_email
import time
from .booking import call_back_email
from .models import Treatments, Customer

def start_assessment(msg, session):
    session['booking_on'] = True
    session.save()
    
def get_response_dates(msg, session):
    print()
    '''
    if not session['calendar_id']:
        response = 'No calendar has been connected to this account yet'
    '''
    
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
                response = f"Hi {first_name} nice to meet you. {response}"
            if prev_key.lower() == 'quantity desired':
                session['summary'][prev_key] = str(extract_numbers(msg))
            
            if prev_key.lower() == 'email':
                if not (is_valid_email(msg)):
                    return "Please provide a valid email address!!"
            if (session['summary']['treatment category'].lower() in ('generic toothache') and count == len(session['question_keys']) - 1):
                    possibilities = worker_three(session['consultation_summary'])
                    response = f"Thanks {session['summary']['client name'].split()[0]} for the information you've provided.<br/><br/>{possibilities} {response}<br/><br/>Click here to view our privacy policy."

            elif (session['summary']['treatment category'].lower() not in ('generic toothache') and count == len(session['question_keys']) - 1):
                response = f"Thanks {session['summary']['client name'].split()[0]},<br/><br/>{response}"
            
            count += 1
            session['count'] = count
            
        else:
            response = session['booking_category']
            first_name = session['summary']['client name'].split()[0]
            if session['no_sale'] == True:
                print('')
                #session.flush()
                return f"Thank you {first_name} for your responses.<br/><br/>You can always come back at a later date to schedule an in-person examination with us."
            else:
                if msg.lower().__contains__('n'):
                    session['summary'][session['question_keys'][count-1]] = msg
                    session['no_sale'] = True
                    session.save()
                    time.sleep(1)
                    print('')
                    return f"No worries {first_name}, it would be very helpful for us if you could briefly explain your reasons for not scheduling an in-person appointment with us today."
                elif msg.lower().__contains__('y'):
                    print('ok')
                    #add send email here
                    session['summary'][session['question_keys'][count-1]] = msg
                    response = get_response_dates(msg, session) #At this stage we should just handle the mailing of the payload
                    session.save()
                    return response
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
    # Client model call - first response to check if and only if a questions can't be matched will it proceed
    print(prob.item(), tag)
    #print(intents)
    if prob.item() >= 0.99999:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                dc['response'] =  random.choices(intent['responses'])[0]
                session['messages'].append({'role':'assistant','content': dc['response']})
    else:
        response = worker_one(session)
        dc['response'] = response
    
    #print(session['messages'])
    session.save()
    return dc


def get_response_callback(msg, session):
    #build this up to handle non funded enquiries
    test_list = ['Whats your full name ?', 'Whats your phone number ?', 'Whats your email address ?', 'Date of Birth','What treatment(s) are you interested in ?','Describe your enquiry in your own words.', 'What time of day should we call ?']
    count = session['count']
 
    if count < len(test_list):
        response = test_list[count]
        if count > 0:
            session['summary'][test_list[count-1]] = msg
        count += 1
        session['count'] = count
        session.save()
    else:
        response = 'Thanks. One of our staff members will be in touch with you shortly regarding your enquiry.'
        session['summary'][test_list[count-1]] = msg
        call_back_email(session)
        #print(session['summary'])
        
    
    
    return response