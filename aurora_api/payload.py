from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
import wikipedia
from langchain.tools import tool
from pydantic import BaseModel, Field
import requests
import datetime
import time
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import os
from django.conf import settings
from .response_node import ResponseNode
from .celeryfuncs import cache_chat_message
from .seleniumworkers import Driver
from .emailfuncs import send_email
from langchain.agents import load_tools
import json
from .language_translation import translate_from_eng





############################ Extractor Payload ##################################################
template = """
Extract the language in a text

"""
prompt = ChatPromptTemplate.from_messages(
    [("system", template),
     ("human", "{input}")
    ])


class Overview(BaseModel):
  """Call this to extract an overview of text input"""
  language:str = Field(description="the language the text is written in for e.g. English, French")
  #sentiment:str = Field(description="the sentiment of the text e.g Positive, Negative, Neutral")
  #text: str = Field(description="the exact text input provided by the user not your response.")
  
 

@tool(args_schema=Overview)
def get_overview(language:str):
  """Run to extract the language of the text, sentiment of the text and the text itself"""
  data = {
    "language": language
  }
  return data
  
######################  Allocation Payload #########################################################
aloc_template="""Allocate the input to the most qualified agent. 
Using this context: 
  Agent Two: If a users asks to speak with a human for further clarification.
  Agent One: Everything not handled by Agent Two.
  
You should respond with 'Agent One' if you allocate to 'Agent One' or 'Agent Two' if you allocate to 'Agent Two'

"""

aloc_prompt= ChatPromptTemplate.from_messages(
    [("system", aloc_template),
     ("human", '{input}')
    ])

class Allocator(BaseModel):
  agent:str = Field(description="The agent to forward the task/input to for further processing")
  input:str = Field(description="The text provided by the user in prompt")

@tool(args_schema=Allocator)
def allocate(agent: str, input: str) -> str:
  """Returns the name of the agent required to handle a user's request"""
  return f"Forward to {agent} input {input}"

#####################  Agent One Payload ###########################################################
agent_template = """

###Instruction###

You are a Therapist who speaks in simple, plain but verbose English. 

You are in a session with me to help me deconstruct and find solutions to my negative emotions. 

Be thorough and always dig deeper into my story. 

You should ask questions and use therapeutic techniques to progress the conversation.

End the interaction by offering me pratical coping mechanisms and strategies for my emotions.

You must ask 1 question at a time !!

###Examples###
Patient: At this point, I'm getting older. I have gray hair. I feel like the clock is ticking. And I don't feel like I will ever find somebody who loves me. I don't feel like I feel like I would have found them already. I feel like I've dated enough people to make that happen and it's not happening. And I don't see anything changing and my depression is through the roof because of it.
Therapist: Okay. So I'm sorry about your breakup and sorry that that kinda led to a cascade of thoughts in your head about what this really means about your future for relationships and about you ultimately. So we're gonna do a practice technique right now, and this technique is called laddering. And what this is gonna help us with is getting some of those negative automatic thoughts.


"""
agent_prompt = ChatPromptTemplate.from_messages(
    [("system", agent_template),
     ("human", "{input}"),
     MessagesPlaceholder(variable_name='agent_scratchpad')
    ])

class OpenMeteoInput(BaseModel):
  latitude: float = Field(..., description="Latitude of the location to get weather for")
  longitude: float = Field(..., description="Longitude of the location to get weather for")

@tool(args_schema=OpenMeteoInput)
def get_current_temparature(latitude:float, longitude:float) -> str:
  """Fetch current weather for given coordinates"""
  BASE_URL = "https://api.open-meteo.com/v1/forecast"

  params = {
      'latitude': latitude,
      'longitude': longitude,
      'hourly': 'temperature_2m',
      'forecast_days': 1
  }

  response = requests.get(BASE_URL, params=params)

  if response.status_code == 200:
    results = response.json()
  else:
    raise Exception(f"Api Request failed with status code {response.status_code}")

  current_utc_time = datetime.datetime.utcnow()
  time_list = [datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')) for time_str in results['hourly']['time']]
  temperature_list = results['hourly']['temperature_2m']

  closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
  current_temperature = temperature_list[closest_time_index]
  return f'The current temperature is {current_temperature}°C'

@tool
def search_wikipedia(query: str) -> str:
  """Run wikipedia search and get page summaries, do not include URL link in your response !"""
  page_titles = wikipedia.search(query)
  summaries = []
  for page_title in page_titles[:3]:
    try:
      wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
      summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
    except(
        #self.wiki_client.exceptions.PageError,
        #self.wiki_client.exception.DisambiguationError,
    ):
      pass
  if not summaries:
    return "No viable results"
  return "\n\n".join(summaries)
  
class GetStreetName(BaseModel):
  street_name:str = Field(description='The name of the street to perform a lookup')

@tool(args_schema=GetStreetName)
def bincollection(street_name: str) -> str:
  """Run this to extract the street name to perform a bin collection schedule check for"""
  if street_name == None:
    response = 'What is the name of your street ?'
  else:
    street_name = street_name.upper()
    result = Driver().getbinday("https://www.southend.gov.uk/directory/51/collection-days-and-recycling-sack-delivery-dates", street_name)
    return result


class GetRegNo(BaseModel):
  reg_no:str = Field(description='The vehicle registration number to search for. Never ABC123 !')
  

'''
@tool(args_schema=GetRegNo)
def checkvehicle(reg_no: str) -> str:
  """Run this to perform a vehicle search using the vehicle registration number provided !"""
  if reg_no == None:
    response = 'What is the vehicle registration number ?'
    return response
  else:
    reg_no = reg_no.upper()
    if len(reg_no.split()) > 0:
      reg_no = ''.join(reg_no.split())
    response = Driver().checkvehtax("https://vehicleenquiry.service.gov.uk/", reg_no)
    return response
'''

@tool(args_schema=GetRegNo)
def checkvehicle(reg_no:str) -> str:
    """Run this to perform a vehicle search using the vehicle registration number provided !"""
    if reg_no == None:
        response = "What is the vehicle registration number ?"
        return response
    else:
        url = 'https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles'
        payload = {"registrationNumber": reg_no}
        api_key = os.environ.get('DVLA_API_KEY')
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.text if response.status_code == 200 else None
       

@tool
def reportvehicle(reg_no:str) -> str:
  """
  Run this always to report an abandoned or untaxed vehicle for the registration number provided, if the vehicle is taxed return a verbose response !
  
  """
  if reg_no == None:
    response = "What is the vehicle registration number ?"
    return response
  response = json.loads(checkvehicle(reg_no))
  print(response)
  if response is not None and response['taxStatus'] == 'Taxed':
    response = 'Sorry you cant report this vehicle as abandoned, it has a valid road tax and therefore is not considered abandoned.'
  return response
  
    
class GetTrashType(BaseModel):
  item:str = Field(description="The waste item to perform a recycle lookup on.")
  
@tool(args_schema=GetTrashType)
def checkdisposal(item: str) -> str:
  """
  Run this to check how to dispose of an item. If the response contains the word 'specific' then invoke the function again.
  
  """
  if item == None:
    response = "What is item you wish to recycle ?"
  else:
    response = Driver().checkrecycling('https://www.southend.gov.uk/directory/53/a-to-z-of-recycling-and-waste', item)
    return response
    

class GetPostCode(BaseModel):
  postcode:str = Field(description='The Postcode to perform the lookup for')
  

@tool(args_schema=GetPostCode)
def checkcatchment(postcode: str) -> str:
  """Run this to check the schools in the catchment area for the Postcode provided"""
  if postcode == None:
    return "What is the Postcode ?"
  else:
    if len(postcode.split()) < 2:
      postcode = f"{postcode.split(postcode[-3])[0]} {postcode[-3]}{postcode.split(postcode[-3])[1]}"
    response = Driver().checkcatchmentarea('https://www.southend.gov.uk/directory/62/school-catchment-areas', postcode)
    return response
    


class LoginDetails(BaseModel):
  candidate_id:str = Field(..., description="6 digit string representing a user's unique candidate ID e.g. 123456")
  password:str = Field(..., description="Alphanumeric string representing the user's password")
  request:str = Field(..., description='Details of record request being made by the user verbatim')
  
@tool(args_schema=LoginDetails)
def login(candidate_id: str, password: str, request:str) -> str:
  """Run this to login to the candidate's user profile"""
  response = Driver().login('https://www.cisi.org/cisiweb2/en/Signin', candidate_id, password, request)
    
  return response
  

@tool
def humancontact() -> str:
  """Run this to initiate contact with a human customer support agent and always provide a verbose response"""
  
  response = "Fill out the form here: https://api.eazibots.com/api/contact-form to send your enquiry and someone will be in touch with you shortly."
  


  
########################### Agent Two Payload ####################################################################
agent_2_temp =  """You are a helpful agent tasked with connecting users to human agents. 

Your job involves collecting summary information from users to process their requests. 
Reiterate the reason you need the information is for the human to contact them!

You must get the users name before a request can be made to a human agent.
You must get additional information about why they want to speak to a human agent and why you're response is not sufficient for them.
"""

agent_2_prompt = ChatPromptTemplate.from_messages(
    [('system', agent_2_temp),
     ('human', '{input}')
    ])
    
class HumanHandOffForm(BaseModel):
  first_name:str = Field(...,description="The first name of the candidate wishing to change details on their record")
  last_name:str = Field(...,description="The last name of the candidate wishing to change details on their record")
  phone_number:str = Field(..., description="The phone number of the candidate requesting the record change")
  email:str = Field(..., description="The email address of the candidate requesting the record change")
  request:str = Field(...,description="The full verbatim request made by the individual")


@tool(args_schema=HumanHandOffForm)
def handoff(first_name:str, last_name:str, phone_number:str, email:str, request:str) -> str:
  '''Run this whenever a user asks to speak with a human person'''
  if first_name in (None, 'John Doe'):
    return 'Whats is your first name ?'
  return None

#####################################################  Agent 3 Payload #############################################################
agent_3_temp =  """Below are some things to ask the user for in a conversational way. You can ask multiple questions but never more than 3!
at a time even if you don't get all the info, don't ask as a list ! Don't greet the user! Don't say Hi. Explain you need to get some info.
If the ask_for list is empty then thank them.
### ask_for list: {ask_for} 

"""

agent_3_prompt = ChatPromptTemplate.from_messages(
    [('system', agent_3_temp)
    ])


@tool
def testfunc(input:list) -> str:
  """Run this to decide what details to request from the user e.g 'phone number' means ask the user for their phone number in a conversational way. If the list is empty thank them."""
  if len(input) > 0:
    ask_for = input.pop(0)
    return ask_for
  else:
    return 'Thanks you'




def agent_router(session, text):
  print(text)
  serp_api = load_tools(['serpapi'])
  agent_tools = [get_current_temparature, bincollection, checkvehicle, reportvehicle, checkcatchment, search_wikipedia, humancontact] + serp_api #add record change tool here.
  agent_chain = ResponseNode(agent_prompt, agent_tools, OpenAIFunctionsAgentOutputParser,'ft:gpt-3.5-turbo-0125:personal:aurora-council:8yEhBV3P')
  response = agent_chain.build_agent(session)
  target = session['language']
  response = translate_from_eng(response, target)
  print(response)
  
  session.save()
  cache_chat_message(session['session_key'], text, response,session['human_agent'])
  print(response)
  
  return response



'''
def agent_router(session, text):
  #tools = [get_overview]
  #extractor_chain = ResponseNode(prompt, tools, OpenAIFunctionsAgentOutputParser)
  #extracts = extractor_chain.use_function(text, "get_overview")
  #print(extracts)
  
  serp_api = load_tools(['serpapi'])
  agent_tools = [search_wikipedia, get_current_temparature, bincollection, checkvehicle, reportvehicle, checkcatchment] + serp_api
  agent_chain = ResponseNode(agent_prompt, agent_tools, OpenAIFunctionsAgentOutputParser,'ft:gpt-3.5-turbo-0125:personal:aurora-council:8yeYWCOm')
    
  agent_2_tools = [handoff]
  agent_2_chain = ResponseNode(agent_2_prompt, agent_2_tools, OpenAIFunctionsAgentOutputParser,'gpt-3.5-turbo')
  
  agent_3_tools = [testfunc]
  agent_3_chain = ResponseNode(agent_3_prompt, agent_3_tools, OpenAIFunctionsAgentOutputParser,'gpt-3.5-turbo')
  
  
  if session['agent_engaged'] == None:
      tools = [allocate]
      allocator_chain = ResponseNode(aloc_prompt, tools, OpenAIFunctionsAgentOutputParser, 'gpt-3.5-turbo')
      allocation = allocator_chain.use_function(session['messages'], "allocate")
      agent_to_use = allocation['agent']
  
  if session['agent_engaged']:
    agent_to_use = session['agent_engaged']
  
  if agent_to_use == "Agent One":
    print(f"Sending input to {allocation['agent']}")
    response = agent_chain.build_agent(session)
    
  if agent_to_use == 'Agent Two':
    ask_for = []
    print(f"Sending input to {agent_to_use}")
    session['human_agent'] = True
    form = agent_2_chain.use_function(session['messages'], 'handoff') # Not response to use
    for k,v in form.items():
      if v in ('', None):
        ask_for.append(k)
      else:
        session['request'][k] = v
   
    #if ask_for is not empty
    #pass into another agent to ask for missing 1 by 1 and return with agent 2 engaged
    if len(ask_for) > 0:
      response = agent_3_chain.build_agent_no_tools(ask_for)
      session['agent_engaged'] = 'Agent Two'
    else:
      response = 'Thank you for using our service your request has been sent to a member of staff who is dealing with your request and will be in touch with you directly.'
      session['agent_engaged'] = None
      send_email(form)
      #save messages here
      session['messages'] = ''
     
  session.save()

  cache_chat_message(session['session_key'], text, response,session['human_agent'])
  return response
'''
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  

