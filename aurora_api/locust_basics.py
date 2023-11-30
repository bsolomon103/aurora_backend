# Locust UI is actually at localhost:8089
from locust import User, HttpUser, TaskSet, task, constant, between
import json, random, time


class UserTasks(TaskSet):
    @task()
    def post_api(self):
        payload = {}
        headers = {'content-type':'application/json'}
        questions = ['hi',
                    "How can I get an adult social care assessment?",
                    "What aid do you provide to carers?",
                    "I want to report a pothole",
                    "I wish to pay a parking fine",
                    "I want to pay my council tax.",
                    "How do i access housing benefits ?",
                    "I want to apply for planning permission.",
                    "I want to register my food business.",
                    "I want to apply for a hackney carriage vehicle license.",
                    "What happens to my recycling ?",
                    "I want to apply for a children's work permit.",
                    "I want to register the birth of my baby."
                    
                    ]
        payload['msg'] = random.choice(questions)
        payload['session_key'] = ''
        payload['origin'] = 'https://262e5fa0c08646e6871bedd3d249507d.vfs.cloud9.eu-west-2.amazonaws.com'
        endpoint = '/'
        with self.client.post(endpoint, 
                              headers=headers,
                              data=json.dumps(payload), 
                              catch_response=True) as response:
            if response is None:
                print(True)
         
    
class BasicUser(HttpUser):
    host = "https://api.eazibots.com/api/response"
    wait_time = between(4,8)
    tasks = [UserTasks]

    def on_start(self):
        print('Entering the store')
    
    def on_stop(self):
        print('Exiting the store')

    



