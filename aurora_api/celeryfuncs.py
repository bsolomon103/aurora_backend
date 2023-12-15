import os
import json
import redis 

from aurora_api.models import Chat

r = redis.from_url('redis://:Aurora24@172.31.40.69:6379/1')

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
    batch_data = [json.loads(data) for data in batch]
    
    print(f"Parsed {len(batch_data)} chat message data for session_key: {session_key}")

    #Create Chat objects for the batch
    chat_objects = [
        Chat(session_id=session_key.decode('utf-8'), 
            message=data.get('message',''), 
            response=data.get('response',''),
            rating=data.get('rating',''), 
            intent=data.get('intent',''))
            for data in batch_data
        ]
    
    print(f"Created {len(chat_objects)} Chat objects for session_key: {session_key}")
 
    Chat.objects.bulk_create(chat_objects)
    print(f"Saved {len(chat_objects)} Chat objects to the database for session_key: {session_key}")

        



        


        

