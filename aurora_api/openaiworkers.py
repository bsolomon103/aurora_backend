import openai 
import os
openai.api_key = os.environ['OPENAI_API_KEY']

#openai.api_key = "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"
#export OPENAI_API_KEY="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"
#export TEST_STRIPE_KEY="sk_test_51NJcbbD1RPWlDlnhXqjIuP8aAsbR3u08EO83FB2FHpfhG8nCgsUbD0fWolN5ifoptsh3ZZsKwOPHzHf1z4P1spU900V7doveLa"
#export WEBHOOK_SECRET="whsec_oNUBClYDh4XalAth8xIZQBpS6ceMMp4i"
import string


def remove_punctuation(text):
    punctuation = string.punctuation
    return ''.join(char for char in text if char not in punctuation)

def worker_one(sessionobj):
    print('worker1')
    chat_history = sessionobj['messages']
    latest_message = chat_history[-1]['content']
    available_treatments = sessionobj['treatment_init']
    probe_question = None
    
    if sessionobj['level1'] and latest_message.lower() == 'no':
        response = "Would you like to complete a pre-appointment questionnaire to assess your suitability and eligibility for this treatment? (Y/N)"
        #f"Would you like to speak to one of our qualified experts to discuss your specific needs? (Y/N)"
        chat_history.append({'role':'user','content': response})
        sessionobj['level1'] = False
        sessionobj['level2'] = True
        return response 
    
    elif sessionobj['level1'] and latest_message.lower() == 'yes':
        latest_message += latest_message + 'i have another question'
        chat_history.append({'role':'user','content': latest_message})

    elif sessionobj['level2'] and latest_message.lower() == 'no':
        response = f"I can arrange a call back, if you'd prefer to speak with one of our qualified professionals instead. (Y/N)"
        sessionobj['level2'] = False
        sessionobj['level3'] = True
        return response 
    
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [
                {'role': 'system', 'content': f"You are a helpful assistant at a UK dentist practice which offers these treatments {available_treatments} your name is Aurora and always responds with 40 words or less. You answer users questions about dental treatments, cost etc all references to 'dentist' should be 'us' or 'we' instead. Your main goal is to ensure the users question has been answered satisfactorily. Don't ask any follow up questions. Limit your responses to 50 words max and never offer a contact number unless asked."}
            ] + chat_history)
    response = response['choices'][0]['message']['content']
    #First ask
    if len(chat_history) >= 3 and not latest_message.lower().__contains__('yes') and not response.__contains__('below'):
        probe_question = f"<br/><br/>Do you have any other questions? (Y/N)"
        sessionobj['level1'] = True
    
    chat_history.append({'role':'assistant','content': response})
    sessionobj['messages'] = chat_history
    
    if probe_question:
        response = response + probe_question
    sessionobj.save()
    print(response)
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
    print(chat_history)
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
def worker_four(msg):
    whitening_treatments = ['teeth whitening', 'hygienist services']
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise. Your job is to decide on the best treatment for a patients discolored teeth based on logs of their conversation {msg} cross referenced with avaialable treatment {whitening_treatments}.  All responses should provide a reason why the proposed treatment is being suggested and limited to 35 words max."},
                        {'role': 'user', 'content': msg}])
   
    response = response['choices'][0]['message']['content']
    if response.__contains__(':'):
        response = response.split(':')[1]
    print(response)
    return response.strip()
    
 
            messages = [
                {'role': 'system', 'content': f"You are a helpful assistant at a UK dentist practice. We respond within 25 words. If the user enquires about booking without specifying treatment, ask if they want a check-up or other treatment."},
                {'role': 'system', 'content': f"Please mention the specific dental treatment you want to book. For example, 'I want to book a cleaning appointment.' Type 'start consultation' for detailed info on a specific treatment, only after choosing one."},
                {'role': 'system', 'content': f"Our practice hours are XX:XX AM/PM to XX:XX AM/PM, Monday to Friday. Let us know how we can assist you."},
                {'role': 'system', 'content': f"If the user wants to sign up (reigister) with your dental practice, then tell them to please type 'start consultation' to begin the registration process."},
            ]
            + chat_history
            )
'''
    
    
