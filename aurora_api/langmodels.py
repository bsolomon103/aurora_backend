from .tools import tools
import time
from langchain.chat_models import ChatOpenAI
from .prompts import aurora_prompt
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chains import RetrievalQAWithSourcesChain, ConversationalRetrievalChain 
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.schema.runnable import RunnableMap, RunnablePassthrough
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI, VertexAI 
from langchain.chat_models import ChatOpenAI
import pickle
from langchain.schema import retriever
import os
import json
from django.conf import settings
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import time
import re
from .celeryfuncs import cache_chat_message
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
import wikipedia
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.tools.render import format_tool_to_openai_function
import requests
from pydantic import BaseModel, Field
import datetime
from langchain.memory import ChatMessageHistory



class OpenMeteoInput(BaseModel):
  latitude: float = Field(..., description="Latitude of the location to get weather for")
  longitude: float = Field(..., description="Longitude of the location to get weather for")
  

@tool
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
  """Run wikipedia search and get page summaries"""
  page_titles = wikipedia.search(query)
  summaries = []
  for page_title in page_titles[:3]:
    try:
      wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
      summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
    except(
        self.wiki_client.exceptions.PageError,
        self.wiki_client.exception.DisambiguationError,
    ):
      pass
  if not summaries:
    return "No viable results"
  return "\n\n".join(summaries)



 
functions = [format_tool_to_openai_function(tool) for tool in [search_wikipedia, get_current_temparature]]
tools = [search_wikipedia, get_current_temparature]

history = ChatMessageHistory()

history.add_user_message("hi!")

history.add_ai_message("whats up?")



class ConversationManager:
    def __init__(self, return_messages=True, memory_key="chat_history"):
        self.memory = {}
        self.return_messages = return_messages
        self.memory_key = memory_key

    def clear(self, session_key):
        # Clear the conversation history for the specified session key
        if session_key in self.memory:
            del self.memory[session_key]
    
    def start_conversation(self, session_key):
    # Clear the conversation history for the specified session key
        try:
            self.memory.clear(session_key)
        except Exception as e:
            print(e)

    def add_message_to_conversation(self, user_id, message):
        # Load existing conversation history from memory
        chat_history = self.memory.load_memory_variables(user_id)

        # Append the new message to the conversation
        key = datetime.datetime.now().isoformat()
        chat_history[key] = message

        # Save the updated conversation history back to memory
        self.memory.save_context(user_id, chat_history)

    def get_chat_history(self, user_id):
        # Retrieve the entire chat history for a user from memory
        chat_history = self.memory.memory_variables(user_id)
        return chat_history

# Example usage
#conversation_memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
#conversation_manager = ConversationManager(conversation_memory)

# Start a new conversation for a user
#user_id = "123"
#conversation_manager.start_conversation(user_id)

# Add messages to the conversation
#conversation_manager.add_message_to_conversation(user_id, "Hello!")
#conversation_manager.add_message_to_conversation(user_id, "How can I help you?")

# Get the entire chat history for the user
#chat_history = conversation_manager.get_chat_history(user_id)
#print(chat_history)



class SaveChats:
    def __init__(self, ChatMessageHistory):
        self.chats = ChatMessageHistory()
        
    
    def add_chat(self, msg, role):
        pass



def chain(session, msg):
    model = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=500).bind(functions=functions)
    prompt = aurora_prompt()
    output = OpenAIFunctionsAgentOutputParser()
    history = ChatMessageHistory()
    history.add_user_message("hi!")
    history.add_ai_message("whats up?")

    

    start = time.time()
    store = FAISS.load_local(os.path.join(settings.BASE_DIR, 'media', 'training_file', os.path.basename(session['customer_name'])), OpenAIEmbeddings())
    retriever = store.as_retriever()
    end = time.time()
    print(f'Time taken to build chain: {start - end}')
    mapp = RunnablePassthrough.assign(
            context = lambda x : retriever.get_relevant_documents(x['input']),
            input =  lambda x : x['input'],
            agent_scratchpad = lambda x : format_to_openai_functions(x["intermediate_steps"])
    )
    chain = mapp | prompt | model | output
    agent_executor = AgentExecutor(agent=chain, tools=tools, verbose=False, memory=memory)
    response = agent_executor.invoke({"input": msg})
    conversation_manager.add_message_to_conversation(session['session_key'], {"role":"assistant","content": response['output']})

    return response['output']


    
    
