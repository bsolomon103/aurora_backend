# Locust UI is actually at localhost:8089
from locust import User, HttpUser, TaskSet, task, constant
import json, random


class UserTasks(TaskSet):
    @task()
    def post_api(self):
        payload = {}
        headers = {'content-type':'application/json'}
        questions = ['hi', 
                     "What are the steps to apply for sheltered housing?",
                     "What is the meaning of CQC?",
                     "What dementia services are available?",
                     "What is a Locality Dementia Navigator ?"]
        payload['msg'] = random.choice(questions)
        endpoint = '/'
        with self.client.post(endpoint, 
                              headers=headers,
                              data=json.dumps(payload), 
                              catch_response=True) as response:
            print(payload['msg'])
            print(response.text)
    

    
    

    

            '''
            if "Sauce Labs Swag Labs app" in response.text and response.status_code == 200:
                response.success()
            else:
                response.failure('Failed to access base url')
            '''
           

class BasicUser(HttpUser):
    host = "http://127.0.0.1:8080/api/response"
    wait_time = constant(2)
    tasks = [UserTasks]

    def on_start(self):
        print('Entering the store')
    
    def on_stop(self):
        print('Exiting the store')

    



