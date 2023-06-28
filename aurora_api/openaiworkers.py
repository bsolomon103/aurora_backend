import openai 
openai.api_key = "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"
import string
append_end = f"Type <img src='https://img.icons8.com/?size=512&id=1XyoV2ktiJK2&format=png'style='height: 20px; width: 25px;' alt='yes'></img> below to explore your options with one of our experts immediately."


def remove_punctuation(text):
    punctuation = string.punctuation
    return ''.join(char for char in text if char not in punctuation)
    
def worker_one(msg):
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. You always provide responses limited to 25 words max. All responses that reference 'the dentist' should be changed to 'us' or 'we' as the dentist able to provide the services suggested."},
                        {'role': 'user', 'content': msg}])
    response = response['choices'][0]['message']['content'].lower()
    response = f"{response.capitalize()}<br/><br/>{append_end}"
    return response

def worker_two(msg, mappings):
    mappings = mappings['booking categories']
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. Your job is to view logs of conversations and determine what category the user input falls into. Use this list {mappings} of categories and return only one of these, your response should be the category and nothing else. For example if the best category is general dentistry then return the answer in the format category: general dentistry and no punctuation afterwards."},
                        {'role': 'user', 'content': msg}])
   
    response = remove_punctuation(response['choices'][0]['message']['content'].lower().split(':')[1].strip())
    return response


def worker_three(msg, questions):
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk providing a consultation for a patient. You must ask a series of questions to deduce the right treatment for them. Limit each response to one question at a time."},
                        {'role': 'user', 'content': msg}])
    response = response['choices'][0]['message']['content'].lower()
    return response
