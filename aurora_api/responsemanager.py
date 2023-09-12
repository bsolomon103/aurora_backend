from .task_utils import get_free_dates, extract_numbers, create_event, timenow
from .openaiworkers import worker_one, worker_two, worker_three, worker_four
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
    booking_duration = treatment_obj.booking_duration if session['no_sale'] == False else 30
    calendar_id = treatment_obj.calendar_id
    

    dates = get_free_dates(session['secret'], calendar_id, booking_duration)
    print(dates[0])
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
                print(msg)
            
                
                #create a booking object here for call back that's unpaid
                #booking_date = session['summary']['booking_date']
                patient_name = session['summary']['client name']
                patient_email = session['summary']['email']
                patient_phone = session['summary']['phone']
                setting = session['summary']['setting']
                #Consider getting booking category from booking category instead of treatment category
                treatment = session['summary']['treatment category'].title()
              
                #Add code here to map treatment to priceable treatments
                summary = session['summary']
                practise_name = session['customer_name']
                calendar_id = session['calendar_id']
                session_id = session['session_key']
                booking_status = 'unpaid'
                practise_obj = Customer.objects.get(name=practise_name)
                #practise_email = practise_obj.email
                practise_phone = practise_obj.phone_number
                quantity = session['summary']['quantity desired'] if 'quantity desired' in session['summary'] else 1
    
                treatment_obj = Treatments.objects.get(customer_name=practise_obj, treatment=treatment)
                practise_email = treatment_obj.calendar_id
                booking_duration = treatment_obj.booking_duration
                
    
                practise_id = session['customer_id'] 
                booking = Booking.objects.create(
                booking_date = msg,
                patient_name = patient_name,
                patient_email = patient_email,
                patient_phone = patient_phone,
                practise_name = practise_name,
                practise_email = practise_email,
                practise_phone = practise_phone,
                treatment = treatment,
                summary = summary,
                booking_status = booking_status,
                price = 0,
                calendar_id = calendar_id, 
                sessionid = session_id,
                booking_duration = 30,
                setting = setting
                )
                create_event(patient_name,treatment,msg,setting,session['calendar_id'],30)
                send_email(booking)
                return f"Thanks {first_name}. A telephone appointment has now been scheduled on your behalf."
            else:
                if msg.lower() == 'call back':
                    session['summary'][session['question_keys'][count-1]] = msg
                    session['no_sale'] = True
                    session.save()
                    time.sleep(1)
                    print('')
                 
                    response = get_response_dates(msg, session) #At this stage we should just handle the mailing of the payload
                    session.save()
                    return response
                 
                elif msg.lower() == 'in-person':
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
   
    if prob.item() >= 0.99:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                dc['response'] =  random.choices(intent['responses'])[0]
                session['messages'].append({'role':'assistant','content': dc['response']})
    else:
        response = worker_one(session)
        dc['response'] = response
    session.save()
    return dc


def get_response_payment(msg, session):
    session['payment'] = True
    key = ['client name', 'phone', 'email', 'date of birth', 'treatment category', 'amount']
    value = ['Whats your full name ?', 'Whats your phone number ?', 'Whats you email address ?', 'Whats your Date of Birth (dd/mm/yyyy)', 'What treatment(s) are you paying for ?', 'How much are you paying today ?']

    count = session['count']
    if count < len(value):
        response = value[count]
        if count > 0:
            if count == 3 and not is_valid_email(msg):
                return 'Please enter a valid email address'
            if count == 5 and not is_valid_treatment(msg, session):
                return 'Please enter a valid treatment'
            session['summary'][key[count-1]] = msg
        count += 1
        session['count'] = count
        session.save()
    else:
        session['summary'][key[count-1]] = int(msg)
        session['summary']['payment_date'] = timenow()
        session['summary']['setting'] = 'payment'
        session.save()
        response = f"Thank you {session['summary']['client name'].split()[0]} for the info you've provided.<br/><br/> Please click the checkout button below to complete your payment and an email confirmation will be sent to you shortly."
        
    return response

        
