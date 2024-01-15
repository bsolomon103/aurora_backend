import os
import json
import redis 

from aurora_api.models import Chat

r = redis.from_url('redis://:Aurora24@172.31.18.131:6379/1')

def cache_chat_message(session_key, message, response, rating=None, intent=None):
    '''Push cached chats into Redis List'''
    #Create a dictionary to represent the chat message
    chat_message = {
        'message': message,
        'response': response,
        'rating': rating,
        'intent': intent
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
    #print(batch)
    batch_data = [json.loads(data) for data in batch]
    message = ' #BREAK#\n '.join([d['message'] for d in batch_data][::-1])
    response = ' #BREAK#\n '.join([d['response'] for d in batch_data][::-1])
    intent = len(batch_data)
    #print(f"Batch {message},{response},{intent}")

    

    

    print(f"Parsed {len(batch_data)} chat message data for session_key: {session_key}")
    
    obj = Chat(session_id=session_key.decode('utf-8'), message=message, response=response, rating='', intent=len(batch_data))
    obj.save()
    

    print(f"Saved Chat objects to the database for session_key: {session_key}")
    
    # Delete data from Redis after successful database save
    r.delete(f'chat_messages:{session_key}')