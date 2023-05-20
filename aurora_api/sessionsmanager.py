from .extract import ModelIngredients
from .task_utils import PerformTask

class SessionManager:
    def __init__(self, sessionobj, origin, msg):
        self.sessionobj = sessionobj
        self.origin = origin
        self.keys = ['file','intents','token','smart_funnel']
        self.msg = msg
 
    def create_session(self):
            print('Session(no)')
            self.sessionobj.create()
            print(f'New Session Created: {self.sessionobj.session_key}')
            seasoning = ModelIngredients(self.origin).extract_data()
            
            # load 'file' and 'intent' into session
            for k in self.keys:
                self.sessionobj[k] = seasoning[k]
                self.sessionobj['process'] = None  
                self.sessionobj['questionasked'] = None 
                self.sessionobj['answers'] = {}
                self.sessionobj['count'] = 0  
            return self.sessionobj
    
    def terminate_process(self):
        self.sessionobj['process'] = None
        self.sessionobj['questionasked'] = None 
        self.sessionobj['answers'] = {}
        self.sessionobj['count'] = 0  
        self.sessionobj.flush()
        return self.sessionobj
    
    def start_process(self):
        process = self.sessionobj['process']
        intents = self.sessionobj['intents']
        for i in intents['intents']:
            if i['tag'] == process + ' questions':
                questions = i['patterns']
            if i['tag'] == 'calender':
                self.sessionobj['calendar_provider'], self.sessionobj['calendar_id'] = i['responses'][0].split(':')[0].strip(), i['responses'][0].split(':')[1].strip()
        self.sessionobj['questions'] = questions
        count = self.sessionobj['count']
        questionasked, task = self.sessionobj['questions'][count].split(':')[0], self.sessionobj['questions'][count].split(':')[1]
        self.sessionobj['questionasked'] = questionasked
        self.sessionobj['task'] = task
        self.sessionobj['answers'][questionasked] = ''
        self.sessionobj['count'] += 1
        return self.sessionobj
    
    def continue_process(self):
        count = self.sessionobj['count']
        questionasked = self.sessionobj['questionasked']             
        output = PerformTask(
                self.msg,
                self.sessionobj['task'], 
                self.sessionobj['token'],
                self.sessionobj['calendar_provider'],
                self.sessionobj['calendar_id']).do_task()
        print(output)
        if output != None and 'start' in output:
            self.sessionobj['event_times'] = output
        self.sessionobj['answers'][questionasked] = self.msg
        questionasked, task = self.sessionobj['questions'][count].split(':')[0], self.sessionobj['questions'][count].split(':')[1]
        self.sessionobj['questionasked'], self.sessionobj['task'] = questionasked, task
        self.sessionobj['count'] += 1
            
        return self.sessionobj
    
    
    def complete_process(self):
        questionasked = self.sessionobj['questionasked']
        self.sessionobj['answers'][questionasked] = self.msg
        if self.sessionobj['event_times']:
            print(self.sessionobj['event_times'])
            event = PerformTask(self.msg, 
                                self.sessionobj['task'], 
                                self.sessionobj['token'],
                                self.sessionobj['calendar_provider'],
                                self.sessionobj['calendar_id']).create_event(self.sessionobj['event_times']['start'],
                                                                            self.sessionobj['event_times']['end'],
                                                                            self.sessionobj['process'],
                                                                            description=self.sessionobj['answers'])                 
        self.sessionobj['questionasked'] = None
        self.sessionobj['process'] = None
        self.sessionobj['count'] = 0
        self.sessionobj['event'] = event
            
        return self.sessionobj
        
    def kill_process(self):
        self.sessionobj['process'] = None
        self.sessionobj['count'] = 0
        del self.sessionobj['intents']
        return self.sessionobj
                