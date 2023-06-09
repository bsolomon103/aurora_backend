# Locust UI is actually at localhost:8089
from locust import User, HttpUser, TaskSet, task, constant, between
import json, random, time


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
            if response is None:
                print(True)
         
    
class BasicUser(HttpUser):
    host = "http://127.0.0.1:8080/api/response"
    wait_time = between(4,8)
    tasks = [UserTasks]

    def on_start(self):
        print('Entering the store')
    
    def on_stop(self):
        print('Exiting the store')

    



