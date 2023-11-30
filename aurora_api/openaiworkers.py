import openai 
import os
openai.api_key = os.environ['OPENAI_API_KEY']
from bs4 import BeautifulSoup
import re
import requests
import json
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
    chat_history = sessionobj['messages']
    latest_message = chat_history[-1]['content']
    print(latest_message)
    available_treatments = sessionobj['treatment_init'] #what does this do !!
    
    tag_pick = [{
          "name": "tagpick",
          "description": "Extract 1 key from the array of tags from the body of input text",
          "parameters": {
            "type": "object",
            "properties": {
              "key": {
                "type": "string",
                "description": "key extracted"
              },
              "value": {
                  "type": "string",
                  "description": "Associated value of key extracted"
                    }
                  },
                  "required": ["key", "value"]
              },
            "required": ["message", "tags"]
          }
        ]


    
    tags = [
              {
                "key": "my mum needs help with her medications",
                "value": "social care services"
              },
              {
                "key": "assistance for individuals who care for an adult with care needs",
                "value": "I'm a carer and i need help"
              },
              {
                "key": "reporting a problem with council managed assets i.e. roads and pavements, highways and roads, traffic and street signs etc",
                "value": "i want to report a pothole"
              },
              {
                "key": "relating to enforcement of violations such as parking fines, traffic wardens, parking restrictions",
                "value": "i wish to pay a parking fine"
              }
              
            ]

    probe_question = None
    prompt = f"The message from the user is {latest_message} and the tags are the following key and value pairs {tags}"
    response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo-0613",
            messages = [
                {'role': 'system', 'content': prompt}
            ],
            functions=tag_pick,
            function_call="auto",
            temperature=0.5)
    print(response)
    response = json.loads(response['choices'][0]['message']['function_call']['arguments'])
    response = response['value']
    chat_history.append({'role':'assistant','content': 'social care services'})
    sessionobj['messages'] = chat_history
    sessionobj.save()
    return response



def extract_second_or_third_string(input_string):
    # Define the regex pattern
    pattern = re.compile(r'^([^:]+):([^:]+)(?::([^:]+))?$')

    # Match the input string against the pattern
    match = pattern.match(input_string)

    # If there's a match, return the third string (group(3)) if it exists, else return the second string (group(2))
    return match.group(3) if match.group(3) else match.group(2) if match.group(2) else None

def worker_two(sessionobj):
    print('1st Pass to OpenAI')
    chat_history = sessionobj['messages']
    tags = [
              {
                "key": "expressing needs of social care services for an adult:assessment",
              },
              {
                "key": "assistance for individuals who care for an adult with care needs:carers"
              },
              {
                "key": "reporting a problem with council managed assets i.e. roads and pavements, highways and roads, traffic and street signs etc:report issue"
              },
              {
                "key": "relating to enforcement of violations such as parking fines, traffic wardens, parking restrictions:transportation infrastructure"
              },
              {
                  "key":"relating to council tax e.g. how do i reduce my council tax:council tax"
              },
              {
                  "key":"relating to housing e.g. i cant afford rent and need help:housing"
              },
              {
                  "key":"relating to planning construction works e.g. i want to demolish a building:planning"
              },{
                  "key":"relating to food businesses and the public e.g. i want to report food poisening at a restaurant:food"
              },
              {
                  "key":"relating to the licensing of taxis e.g how do i renew my taxi license:taxi"
              },
              {
                  "key":"relating waste collection, disposal and recycling e.g. what do i do about garden waste:waste"
              },
              {
                  "key":"relating to childrens services e.g. i want a school admissions form:childrens"
              },
              {
                  "key":"relating to certificates key events in life e.g. birth, death, marriage, citizenship certificates:certificates"
              }
              
            ]
    response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. Using this {chat_history} match users to a treatment category for a virtual assessment. This is the list of treatments here {tags}, match to 1 value and return its associated key. Your response should be the category name only. All your responses should follow the format category: your chosen category. Pre-wedding polish should map to dental hygiene"}]
            )
    response = response['choices'][0]['message']['content'].lower()
    sessionobj['messages'] = chat_history
    if response.__contains__(':'):
        response = extract_second_or_third_string(response)
    chat_history.append({'role':'assistant','content': response.strip()})
    return response.strip()



def worker_three(sessionobj):
    print('Pull team info')
    chat_history = sessionobj['messages']
    msg = chat_history[-2:]
    tags = [
              {
                "key": "expressing needs of social care services for an adult:assessment",
              },
              {
                "key": "assistance for individuals who care for an adult with care needs:carers"
              },
              {
                "key": "reporting a problem with council managed assets i.e. roads and pavements, highways and roads, traffic and street signs etc:report issue"
              },
              {
                "key": "relating to enforcement of violations such as parking fines, traffic wardens, parking restrictions:transportation team"
              },
              {
                  "key":"relating to council tax e.g. how do i reduce my council tax:council tax team"
              },
              {
                  "key":"relating to housing e.g. i cant afford rent and need help:housing team"
              },
              {
                  "key":"relating to planning construction works e.g. i want to demolish a building:planning"
              },{
                  "key":"relating to food businesses and the public e.g. i want to report food poisening at a restaurant:food"
              },
              {
                  "key":"relating to the licensing of taxis e.g how do i renew my taxi license:taxi"
              },
              {
                  "key":"relating waste collection, disposal and recycling e.g. what do i do about garden waste:waste"
              },
              {
                  "key":"relating to childrens services e.g. i want a school admissions form:childrens"
              },
              {
                  "key":"relating to certificates key events in life e.g. birth, death, marriage, citizenship certificates:certificates"
              },
              {
                  "key":"relating to business rates:business rates team"
              }
              
            ]
    
    response = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. Using this {chat_history} match users to a treatment category for a virtual assessment. This is the list of treatments here {tags}, match to 1 value and return its associated key. Your response should be the category name only. All your responses should follow the format category: your chosen category. Pre-wedding polish should map to dental hygiene"}]
            )
    response = response['choices'][0]['message']['content'].lower()
    sessionobj['messages'] = chat_history
    if response.__contains__(':'):
        response = extract_second_or_third_string(response)
    chat_history.append({'role':'assistant','content': response.strip()})
    return response.strip()
    
    