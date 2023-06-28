from .task_utils import get_free_dates
from .openaiworkers import worker_one, worker_two, worker_three
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import torch
import random
from .booking import costs
from .emailcheck import is_valid_email
#from .models import Treatments

def get_response_dates(msg, session):
    session['booking_on'] = True
    if not session['calendar_id']:
        response = 'No calendar has been connected to this account yet'
    else:
        dates = get_free_dates(session['secret'])
        response = f"Please choose a date and time that works for you<br/><br/>{dates[0]}"
        session.save()
    return response

def get_response_booking(msg, session):
    if 'questions' not in session:
        session['summary']['booking date-time'] = msg
        category = worker_two(session['messages'], session['mappings'])
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
            prev_key = session['question_keys'][count-1]
            
            #move into a different file with validations across the key i.e. patient status 
            if prev_key == 'email':
                if not (is_valid_email(msg)):
                    return "Please provide a valid email address!!"
   

            
            response = session['questions'][question_key]
            print(msg, response)
            session['summary'][prev_key] = msg
            count += 1
            session['count'] = count
            #return response
        else:
            response = session['booking_category']
            session['summary'][session['question_keys'][count-1]] = msg
            response = f"Thank you for the info you've provided.<br/><br/> Please click the checkout button below to complete your booking."
            print(session['summary'])
 
    session.save()
    
    return response

def get_response_aurora(msg, model, all_words, tags, session, device):
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
    #print(prob.item(), tag)
    if prob.item() >= 0.99:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                dc['response'] =  random.choices(intent['responses'])[0]
    else:
        response = worker_one(msg)
        dc['response'] = response
    session['messages'] += msg
    session.save()
    return dc

    