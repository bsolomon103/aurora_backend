from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableMap,RunnablePassthrough
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools.render import format_tool_to_openai_function
#from langchain_core.utils.function_calling import convert_to_openai_function 
from langchain.chat_models import ChatOpenAI
#from langchain_community.chat_models import ChatOpenAI
import os
import time
from langchain.embeddings import OpenAIEmbeddings
from django.conf import settings
import faiss
from langchain.vectorstores import FAISS
import re
from .apps import vector_store



class ResponseNode:
  """
  Builds configurable base chain for use in iso or for an agent.
  Attributes:
    prompt(str): ChatPromptTemplate to package input template.
    tools(list): List of tools to bind as functions to model and/or AgentExecutor.
    output_parser: Output parser to structure and standardise the output
  """
  def __init__(self, prompt,tools, output_parser, model):
    self.prompt = prompt
    self.model = ChatOpenAI(model_name=model, temperature=0, max_tokens=1000)
    self.tools = tools
    self.parser = output_parser
    self.functions = [format_tool_to_openai_function(t) for t in self.tools]
    
  
  def clean_chain(self, obj):
    chain = self.prompt | self.model | self.parser()
    return chain.invoke({'input': obj})

  def retriever(self, session):
    """
    start = time.time()
    store = FAISS.load_local(os.path.join(settings.BASE_DIR, 'media', 'training_file', os.path.basename(session['customer_name'])),OpenAIEmbeddings())
    end = time.time()
    print(f"Time taken to load db: {end - start}")
    """
    store = vector_store
    return store.as_retriever()
  
  def postprocessor(self, text):
    # Find everything within square brackets
    matches = re.findall(r'\[([^]]+)\]', text)
    
    return matches[0] if len(matches) > 0 else None
      
      
  def use_function(self, text, function):
    """
    Allows access to specific functionality on the chain.
    Attributes:
      text(str): Input message received as part of the prompt
      function(str): Name of the function to call
    """
    self.extractmodel = self.model.bind(functions=self.functions, function_call={"name":function})
    chain = self.prompt | self.extractmodel | self.parser()
    response = chain.invoke({"input": text})
    self.model = None
    return response.tool_input
  
  def use_tool(self, text, function):
    """
    Allows access to specific functionality on the chain.
    Attributes:
      text(str): Input message received as part of the prompt
      function(str): Name of the function to call
    """
    self.extractmodel = self.model.bind(functions=self.functions, function_call={"name":function})
    chain = self.prompt | self.extractmodel | self.parser()
    response = chain.invoke({"input": text})
    self.model = None
    return response.tool_input

  
    

  def build_agent(self, session):
    """
    Build an agent with document retrieval functionality.
    Remember to use custom inputs eg prompt with context and agent scracthpad
    Attributes:
      retriever: Retriever required to get relevant documents from vector store
      text: Input message received as part of user prompts

    """

    retriever = self.retriever(session)
    self.agentmodel = self.model.bind(functions=self.functions)
    map = RunnablePassthrough.assign(
            context = lambda x : retriever.get_relevant_documents(x['input']),
            input =  lambda x : x['input'],
            agent_scratchpad = lambda x : format_to_openai_functions(x["intermediate_steps"])
            )

    chain = map | self.prompt | self.agentmodel | self.parser()
    try:
        agent = AgentExecutor.from_agent_and_tools(agent=chain, tools=self.tools, verbose=True, return_only_outputs=True, handle_parsing_errors=True)
        response = agent.invoke({"input": session['messages']})
        print(response)
        current_messages = session['messages']
        current_messages = current_messages + f"assistant: {response['output']}\n"
        session['messages'] = current_messages
        session.save()
          
        response = response['output']
        def url_check(text):
          urls = re.findall(r'\b(?:https?|ftp):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', text)
          unique_urls = set(urls)
          return len(urls) == len(unique_urls)
         
          
        if response.__contains__('assistant:'):
            response = response[11:]
            #response = ''.join(response)
              
        x = self.postprocessor(response)
        
        if x != None and url_check(response) == False:
            response = response.replace(f"[{x}]", '🖳') 
        elif x != None and url_check(response):
          response = response.replace('[', '').replace(']', '')
        
  
        return response
    except Exception as e:
        print(e)
    
  
  def build_agent_no_tools(self, text):
    """Build a blank slate agent with prompt and some input context"""
    #print(summary)
    self.agentmodel = self.model
    map = RunnableMap(
          {"ask_for": lambda x : x['ask_for']
    })
    chain = map | self.prompt | self.agentmodel | self.parser()
    agent = AgentExecutor(agent=chain, tools=self.tools, verbose=True, return_only_outputs=True)
    response = agent.invoke({"ask_for": text})
          
    response = response['output']
    if response.lower().__contains__('assistant:'):
            response = response[11:]
            #response = ''.join(response)
    print(response)
    return response
    
    
        

        