import datefinder
import os
import pickle
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import string

class PerformTask:
    def __init__(self, message, task, tokenfile, provider, calendar_id):
        self.message = message
        self.task = task 
        self.token = tokenfile
        self.provider = provider
        self.calendar_id = calendar_id
        self.dc = {}

    def do_task(self):
        if (self.task.strip() == 'check availability'):
            return self.check_availability()
             
    def check_availability(self):
        date = list(datefinder.find_dates(self.message))
        date = date[0] if len(date) > 0 else 'No date found'
        start = date - timedelta(minutes=60)
        end  = start  + timedelta(minutes=60)
        start = start.isoformat(timespec='milliseconds') + 'z'
        end = end.isoformat(timespec='milliseconds') + 'z'
        request_body = {
                        "timeMin": start,
                        "timeMax": end,
                        "timeZone": 'UTC',
                        "groupExpansionMax": 1,
                        "calendarExpansionMax" : 1,
                        "items": [
                                    {
                                    "id": self.calendar_id
                                    }
                                ]
                        }
        credentials = pickle.load(open(os.path.abspath('files\\' + self.token), 'rb'))
        service = build('calendar', 'v3', credentials=credentials)
        free_busy  = service.freebusy().query(body=request_body).execute()
        if len(free_busy['calendars'][self.calendar_id]['busy']) == 0:
            self.dc['start'], self.dc['end'] = start, end
            return  self.dc
        else:
            # rerun here till a free slot is found
            pass
    
    def create_event(self, start, end, summary, duration=1, description=None, location=None):
        text  = ''
        for k,v in description.items():
            load = k.translate(k.maketrans(' ',' ', '?.')) + '---' + v
            text += load + '.\n'
        event = {
                    'summary': summary.capitalize(), # this will be the intent tag on backend
                    'location': 'Southend On Sea', # if room booking service is available write here/default loc
                    'description': text,
                    'start': {
                            'dateTime': start,
                            'timeZone': 'Europe/London',
                        },
                    'end': {
                            'dateTime': end,
                            'timeZone': 'Europe/London',
                        },
                    'reminders': {
                            'useDefault': False,
                            'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 10},
                            ],
                        },
                        }
        credentials = pickle.load(open(os.path.abspath('files\\' + self.token), 'rb'))
        service = build('calendar', 'v3', credentials=credentials)
        try:
            event  = service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return 'Event creation succeeded'
        except:
            return 'Event creation failed'
       
            


