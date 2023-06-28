import datefinder
import os
import pickle
import dill
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import string
from .descriptformat import DescFormatter
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import os

scopes = ['https://www.googleapis.com/auth/calendar']


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
        return self._check_availability(start)
    
    def _check_availability(self, start):
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
        credentials = pickle.load(open(os.path.abspath('media/' + self.token), 'rb'))
        service = build('calendar', 'v3', credentials=credentials)
        free_busy  = service.freebusy().query(body=request_body).execute()
        slot_len = len(free_busy['calendars'][self.calendar_id]['busy'])
        if slot_len == 0:
            print('Free timeslot')
            self.dc['start'], self.dc['end'] = start, end
            return self.dc
        else:
            print('Timeslot taken')
            start = start[:-5]
            start = list(datefinder.find_dates(start))[0] + timedelta(minutes=60)
            return self._check_availability(start)
            
        
            
    def create_event(self, start, end, summary, duration=1, description=None, location=None):
        text  = ''
        formatt = DescFormatter(summary).skeleton()
        for k,v in enumerate(description):
        
            payload = formatt[k] + ': ' + description[v]
            #load = k.translate(k.maketrans(' ',' ', '?.')) + '---' + v
            text += payload + '.\n'
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
        credentials = pickle.load(open(os.path.abspath('media/' + self.token), 'rb'))
        service = build('calendar', 'v3', credentials=credentials)
        try:
            event  = service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return 'Event creation succeeded'
        except:
            return 'Event creation failed'
    
    
class FreeSlotChecker:
    def __init__(self, credentials):
        #self.credentials = pickle.load(open(os.path.abspath('media/' + credentials), 'rb'))
        self.credentials = credentials
        self.utc = pytz.timezone('UTC')
        self.start_time = datetime.now(self.utc).replace(minute=0, second=0, microsecond=0)
        self.start_time_str = self.start_time.isoformat()
        self.end_time = self.start_time + timedelta(days=1)
        self.end_time_str = self.end_time.isoformat()
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def refresh_token(self):
        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            #dill.dump(self.credentials, open(os.path.abspath('media/' + self.credentials), "wb"))
    
    def get_free_utc_slots(self):
        # Make the request to retrieve the free/busy information
        free_busy = self.service.freebusy().query(body={
            'timeMin': self.start_time_str,
            'timeMax': self.end_time_str,
            'items': [{'id': 'primary'}]  # 'primary' refers to the primary calendar of the authenticated user
        }).execute()
        
        # Extract the free slots from the response
        busy_slots = free_busy['calendars']['primary']['busy']
        free_slots = []
           
        # Calculate the free slots within the time range
        current_time = self.start_time
      
        while current_time < self.end_time:
            slot_start = current_time
            slot_end = current_time + timedelta(minutes=60)
            slot = {'start': slot_start.isoformat(), 'end': slot_end.isoformat()}

            # Check if the slot is not part of any busy slot
            is_free = True

            for busy_slot in busy_slots:
                busy_start = self.utc.localize(datetime.strptime(busy_slot['start'], '%Y-%m-%dT%H:%M:%SZ'))
                busy_end = self.utc.localize(datetime.strptime(busy_slot['end'], '%Y-%m-%dT%H:%M:%SZ'))
                
                if (slot_start >= busy_start and slot_end <= busy_end):
                    is_free = False
                    break
            if is_free:
                free_slots.append(slot)
            current_time += timedelta(minutes=60)
            
        return free_slots
               
    def convert_brtz(self):
        utc_slots = self.get_free_utc_slots()
        brit_slots = []
        british_tz = pytz.timezone('Europe/London')
        for i,j in enumerate(utc_slots):
            if i > 0:
                slot = {}
                start_time = datetime.strptime(j['start'], '%Y-%m-%dT%H:%M:%S%z').astimezone(british_tz).isoformat()
                end_time = datetime.strptime(j['end'], '%Y-%m-%dT%H:%M:%S%z').astimezone(british_tz).isoformat()
                
                slot['start'] = start_time
                slot['end'] = end_time
                brit_slots += [slot]
        return brit_slots

def get_free_dates(client_secret_file):
    client_secret_file = os.path.abspath('media/'+ client_secret_file)
    credentials = Credentials.from_service_account_file(client_secret_file,scopes=scopes)
    x = FreeSlotChecker(credentials).convert_brtz()
    return x


