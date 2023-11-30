from langchain.chains import RetrievalQAWithSourcesChain, ConversationalRetrievalChain 
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap
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
from .tools import search_wikipedia

from rest_framework.response import Response

# to change model go to OpenAI website and add below as model_name


def build_chain(session, question):
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', max_tokens=120, temperature=0)
    start = time.time()
    store = FAISS.load_local(os.path.join(settings.BASE_DIR, 'media', 'training_file', os.path.basename(session['customer_name'])), OpenAIEmbeddings())
    retriever = store.as_retriever()
    end = time.time()
    print(f'Time taken to build chain: {start - end}')
    template = """Answer the question based only on the following context: {context} Question: {question}. Limit your responses to 30 words max."""
    prompt = ChatPromptTemplate.from_template(template)
    chain = RunnableMap({
    "context": lambda x: retriever.get_relevant_documents(x["question"]),
    "question": lambda x: x["question"]
    }) | prompt | llm | StrOutputParser()
    #data = chain.invoke({"question":question})
    #print(data)
    #return data
    
    bag = ''
    count = 0 
    for chunk in chain.stream({"question": question}):
        data = json.dumps({"session_key":session['session_key'],"response": chunk.strip()})
        bag += chunk
        count += 1
        session['count'] = count
        if chunk == '.' and count > 0 and not session['cached']:
            cache_chat_message(session['session_key'], question, bag, 'like',session['intent'])
            print(bag) #celery cache object here to capture server response (poll)
            session['cached'] = True
        session.save()
        yield data




def label_strip(url):
    x = (url.split('/'))[-1:]
    if len(x[0]) < 3:
        x = (url.split('/'))[-2:]
        x = ' '.join(' '.join(x).capitalize().split('-'))
        return x
        
    else:
        x = (url.split('/'))[-1:][0].split('-')
        return ' '.join(x).capitalize()


    
def format_emails(text):
    # Regular expression for matching email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Find all email addresses in the text
    matches = re.finditer(email_pattern, text)

    # Replace each email address with a formatted HTML anchor tag
    formatted_text = text
    for match in matches:
        email = match.group()
        formatted_text = formatted_text.replace(email, f'<a href="mailto:{email}">{email}</a>')

    return formatted_text
    





