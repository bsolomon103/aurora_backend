import os
import time
import json
import redis 
from aurora_api.models import Chat
from .response_node import ResponseNode
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

r = redis.from_url('redis://:Aurora24@172.31.18.131:6379/1')

############################ Extractor Payload ##################################################
template = """

Council Tax:  E.g. How do i pay my council tax?
Housing Benefits: E.g. What is eligibility criteria for receiving housing benefits?
Business Rates: E.g. I want to pay my business rates.
Abandoned and Untaxed Vehicles: E.g. There's a car parked outside my house, can i have it removed?
Report It: E.g. I want to report a pothole
Parking Fines: E.g. I want to appeal a PCN.
Waste & Recycling: E.g. I am 65 years old and need help with my bins.
Register It: E.g. How can i make an appointment to register my new born?

"""
prompt = ChatPromptTemplate.from_messages(
    [("system", template),
     ("human", "{input}")
    ])


class Overview(BaseModel):
  """Call this to extract an overview of text input"""
  intent:str = Field(description='the purpose of the users prompt or statement i.e.\
                                  Council Tax,\
                                  Housing Benefits, Business Rates,\
                                  Abandoned and Untaxed Vehicles,\
                                  Report It, Parking Fines, \
                                  Waste & Recycling, Register It')

  
@tool(args_schema=Overview)
def get_overview(intent:str):
  """Run to extract the language of the text, sentiment of the text and the text itself"""
  data = {
    "intent": intent
  }
  return data
  
#################################################################################################################################################################
reason_template = """

Discounts: E.g. How do i apply for council tax reduction. I can't afford my bill.
Pay E.g. I want to pay my business rates
Appeals & Reconsiderations E.g. I want to appeal a PCN (Parking Fine)
Eligibility E.g. What is eligibility criteria for receiving housing benefits?
Abandoned Vehicle E.g. There's a car parked outside my house, can i have it removed?
Vehicle Information E.g. Tell me something about this car ?
Bulky Waste E.g. I want to arrange the collection and disposal of an old fridge. 
Garden Waste E.g. I have garden waste that I want collected
Recycling E.g. What items can go in the pink recycling sacks?
New Bin E.g. I want to order a new bin.
Waste Collection E.g. When are the bins collected on westborough road
Missed Collection E.g. My rubbish has not been collected, what should i do?
Assisted Collection E.g. I am 65 years old and need help with my bins.
Schools Catchment E.g. What primary schools are in my area?
Potholes E.g. I want to report a pothole
Birth E.g. How can i make an appointment to register my new born.
Death E.g. There's been a bereavement in the family and I want to register a death
Marriage & Civil Union E.g. Me and my partner would like to register a civil union.
Still Birth E.g. I had a still birth. What do i do?
Vows Renewal E.g. Me and my partner would like to renew our vows.
Lost Or Duplicates E.g. I lost my sons birth certificate. How do i order a duplicate?
Naming Ceremony: E.g. I want to book a naming ceremony for my daughter.


"""
reason_prompt = ChatPromptTemplate.from_messages(
    [("system", reason_template),
     ("human", "{input}")
    ])

  
class Subview(BaseModel):
  """Call this to extract a reason from the text input"""
  reason:str = Field(description="""the reason for the users prompt or statement i.e.\
                                    Discounts, Pay, Appeals & Reconsiderations,\
                                    Eligibility, Abandoned Vehicle, Vehicle Information,\
                                    Bulky Waste, Garden Waste, Recycling, New Bin\ 
                                    Waste Collection, Missed Collection, Assisted Collection\
                                    Schools Catchment, Potholes, Birth, Death,\
                                    Marriage & Civil Union, Still Birth,\ 
                                    Vows RenewalsLost Or Duplicate,\
                                    Naming Ceremony.
                                  """)

  
@tool(args_schema=Subview)
def get_subview(reason:str):
  """Run to extract the reason for the users request"""
  data = {
    "reason": reason
  }
  return data
  




####################################### Extractor Instances############################################################################


def cache_chat_message(session_key, message, response, human_agent):
    '''Push cached chats into Redis List'''
    #Create a dictionary to represent the chat message
    chat_message = {
        'message': message,
        'response': response,
        'human_agent': human_agent
    }
    
    #Serialize the data
    serialized_data = json.dumps(chat_message)
 
    session_key = session_key.encode('utf-8')
    r.lpush(f'chat_messages:{session_key}', serialized_data)
    if not r.sismember('session_keys_set', session_key):
        #If it doesn't exist, add it to the set
        r.sadd('session_keys_set', session_key)
  

def save_data_to_db(session_key, batch_size=100):
    '''Pulls cached chats out of the Redis List'''
    #Populates chat_messages with the entire content of the list for each session
    chat_messages = r.lrange(f'chat_messages:{session_key}', 0, -1)
    print(f"Starting save_data_to_db for session_key: {session_key}")

    
    #Process and save data in batches
    batch = chat_messages
    print(batch)
    batch_data = [json.loads(data) for data in batch]
    message = ' #BREAK#\n '.join([d['message'] for d in batch_data][::-1])
    response = ' #BREAK#\n '.join([d['response'] for d in batch_data][::-1])
    chats = len(batch_data)
    #intent = (' #BREAK#\n '.join([d['intent'] for d in batch_data if d['intent'] != 'Greeting'][::-1])).split(' #BREAK#')[0]
    #intent = intent if intent != '' else 'Greeting'
    print(1)
    time.sleep(0.3)
    tools = [get_overview]
    intent_chain = ResponseNode(prompt, tools, OpenAIFunctionsAgentOutputParser, 'gpt-3.5-turbo')

    sub_tool = [get_subview]
    reason_chain = ResponseNode(reason_prompt, sub_tool, OpenAIFunctionsAgentOutputParser, 'gpt-3.5-turbo')

    intent = intent_chain.use_function(message, 'get_overview')
    print(f"Intent:{intent}")
    reason = reason_chain.use_function(message, 'get_subview')
    print(f"Reason:{reason}")
    try:
        human_agent = [d['human_agent'] for d in batch_data if d['human_agent']][0]
    except:
        human_agent = False

    chats = len(batch_data)
    #print(f"Batch {message},{response},{intent}")

    print(f"Parsed {len(batch_data)} chat message data for session_key: {session_key}")
    
    obj = Chat(session_id=session_key.decode('utf-8'), message=message, response=response, chats=chats, intent=intent['intent'], reason=reason['reason'], human_agent=human_agent)
    obj.save()
    

    print(f"Saved Chat objects to the database for session_key: {session_key}")
    
    # Delete data from Redis after successful database save
    r.delete(f'chat_messages:{session_key}')