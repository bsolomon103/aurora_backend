import openai 
import os
openai.api_key = os.environ['OPENAI_API_KEY']
from bs4 import BeautifulSoup
import re

#openai.api_key = "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"
#export OPENAI_API_KEY="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"
#export TEST_STRIPE_KEY="sk_test_51NJcbbD1RPWlDlnhXqjIuP8aAsbR3u08EO83FB2FHpfhG8nCgsUbD0fWolN5ifoptsh3ZZsKwOPHzHf1z4P1spU900V7doveLa"
#export WEBHOOK_SECRET="whsec_oNUBClYDh4XalAth8xIZQBpS6ceMMp4i"
import string


def emailcheck(txt):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    matches = re.findall(pattern, txt)
    if matches:
        for match in matches:
            res = txt.split(match)
            return f"{res[0]}<a href='mailto:{match}'>email</a>{res[1]}"
    else:
        return txt

def urlcheck(txt):
    url = r'https?://[^\s/$.?#].[^\s]*'
    matches = re.findall(url, txt)
    if matches:
        for match in matches:
            #print(match)
            res = txt.split(match)
        return f"{res[0]}{match}{res[1]}"
    else:
        return txt

def remove_punctuation(text):
    punctuation = string.punctuation
    return ''.join(char for char in text if char not in punctuation)

def worker_one(sessionobj):
    print('worker1')
    print(sessionobj['booking_on'])
    chat_history = sessionobj['messages']
    #print(chat_history)
    latest_message = chat_history[-1]['content']
    print(latest_message)
    #available_response = sessionobj['']
    available_treatments = sessionobj['treatment_init']
    probe_question = None
    


    response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = [
                {'role': 'system', 'content': f"You are a helpful assistant working for Southend City Council local authority and your name is Aurora and always responds with 40 words or less."}
            ] + chat_history,
            temperature=0.2)
    response = response['choices'][0]['message']['content']
    response = latest_message if response == '' else response
    
    chat_history.append({'role':'assistant','content': response})
    sessionobj['messages'] = chat_history

    sessionobj.save()
    #print(response)
    return response



def worker_two(sessionobj, mappings):
    print('worker2')
    category = mappings['booking categories']
    chat_history = sessionobj['messages']
    services = sessionobj['treatment_init']
    response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. Using this {chat_history} match users to a treatment category for a virtual assessment. This is the list of treatments here {category}, return only one of these. Your response should be the category name only. All your responses should follow the format category: your chosen category. Pre-wedding polish should map to dental hygiene"}]
            )
    response = response['choices'][0]['message']['content'].lower()
    print(response)
    print(sessionobj['booking_on'])
    sessionobj['messages'] = chat_history
    if response.__contains__(':'):
        response = response.split(':')[1]
    chat_history.append({'role':'assistant','content': response.strip()})
    return response.strip()


def worker_three(msg):
    #print(msg)
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise. Your job is to offer 2 possible diagnoses to a patients problem. Use this log of {msg} to decide on what their treatment should be.Limit your responses to 35 words.  All responses that reference 'the dentist' should be changed to 'us' or 'we' as the dentist able to provide the services suggested."},
                        {'role': 'user', 'content': msg}])
    #print(response)
    response = response['choices'][0]['message']['content']
    return response


def worker_four(msg):
    treatments = ['invisalign', 'veneers', 'inman']
    #{'invisalign':{'cost':'£1950-£5400','examination cost':'600','examination offer':'Extensive Consultation including: Smile design analysis, study casts, radiographic analysis, photos and treatment planning'}, 'inman aligners':'£1760', 'braces':'£2000-£3800', 'veneers':'£730'}
    
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f" You are a helpful assistant that works for a dentist practise. Your job is to map users input to 1 of these available treatments {treatments} this is a python list and you're response should be the treatment name only."},
                        {'role': 'user', 'content': msg}])
    #print(response)
    response = response['choices'][0]['message']['content']
    return response
    




'''
def convert_html_to_links(text):
    soup = BeautifulSoup(text, 'html.parser')
    for a in soup.find_all('a'):
        link_text = a.get_text()
        href = a['href']
        link = f"<a href='{href}' target='_blank'>{link_text}</a>"
        text = text.replace(str(a), link)
    return text
    
    


def worker_one(sessionobj):
    print('worker1')
    print(sessionobj['booking_on'])
    chat_history = sessionobj['messages']
    latest_message = chat_history[-1]['content']
    available_treatments = sessionobj['treatment_init']
    probe_question = None
    

    
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [
                {'role': 'system', 'content': f"You are a helpful assistant at a UK local authority which offers these services {available_treatments} your name is Aurora and always responds with 40 words or less. You answer users questions about services, costs etc. Your main goal is to ensure the users question has been answered satisfactorily. Don't ask any follow up questions. Limit your responses to 40 words max and never ever ask the user if they would like to schedule or book an appointment. If the response contains URL ensure these are clickable links"}
            ] + chat_history)
            
    response = response['choices'][0]['message']['content']
   

    #response = "You can visit the <b><a href='https://livewellsouthend.com/kb5/southendonsea/directory/advice.page?id=6EVktPY9muo' target='_blank'>Livewell Southend Website</a></b> for more information."

    #response = convert_html_to_links(response)
    

    
    #response = convert_html_to_links(response)
    #First ask
    
    if len(chat_history) >= 3 and not latest_message.lower().__contains__('yes') and not response.__contains__('below') and not response.__contains__('?'):
        probe_question = f"<br/><br/>Do you have any other questions? (Y/N)"
        sessionobj['level1'] = True

    
    chat_history.append({'role':'assistant','content': response})
    sessionobj['messages'] = chat_history
    
    if probe_question:
        response = response + probe_question
    sessionobj.save()
    #print(response)
    return response



def worker_two(sessionobj, mappings):
    print('worker2')
    category = mappings['booking categories']
    chat_history = sessionobj['messages']
    services = sessionobj['treatment_init']
    response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a local authority in the uk. Using this {chat_history} match users to a service category for a virtual booking. This is the list of services here {category}, return only one of these. Your response should be the category name only. All your responses should follow the format category: your chosen category."}]
            )
    response = response['choices'][0]['message']['content'].lower()
    print(response)
    print(sessionobj['booking_on'])
    sessionobj['messages'] = chat_history
    if response.__contains__(':'):
        response = response.split(':')[1]
    chat_history.append({'role':'assistant','content': response.strip()})
    return response.strip()
'''

