import datefinder
import os
import re
from word2number import w2n
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
from aurora_api.models import AppCredentials

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
        
        start = date - timedelta(minutes=10)
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
            start = list(datefinder.find_dates(start))[0] + timedelta(minutes=10)
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
    def __init__(self, credentials, calendar_id, booking_duration):
        #self.credentials = pickle.load(open(os.path.abspath('media/' + credentials), 'rb'))
        self.credentials = credentials
        self.utc = pytz.timezone('UTC')
        self.start_time = datetime.now(self.utc).replace(minute=0, second=0, microsecond=0)
        self.start_time_str = self.start_time.isoformat()
        self.end_time = self.start_time + timedelta(days=20)
        self.end_time_str = self.end_time.isoformat()
        self.calendar_id = calendar_id
        self.booking_duration = booking_duration
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
            'items': [{'id': self.calendar_id}]  # 'primary' refers to the primary calendar of the authenticated user
        }).execute()
        
        # Extract the free slots from the response
        busy_slots = free_busy['calendars'][self.calendar_id]['busy']
        free_slots = []
           
        # Calculate the free slots within the time range
        current_time = self.start_time
      
        while current_time < self.end_time:
            slot_start = current_time
            slot_end = current_time + timedelta(minutes=self.booking_duration)
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
            current_time += timedelta(minutes=self.booking_duration)
            
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

def get_free_dates(client_secret_file, calendar_id, booking_duration):
    #client_secret_file = os.path.abspath('media/'+ client_secret_file)
    credentials = Credentials.from_service_account_file(client_secret_file,scopes=scopes)
    x = FreeSlotChecker(credentials, calendar_id, booking_duration).convert_brtz()
    return x
    
def convert_utc(datetimestr, booking_duration):
    utc = pytz.timezone('UTC')
    converted = datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M:%S%z').astimezone(utc)
    start = converted.isoformat()
    end = (converted + timedelta(minutes=booking_duration)).isoformat()
    return start, end
    

def create_event(patient_name,treatment, timeobj, setting, calendar_id, booking_duration, description=None, location=None):
    setting = setting
    name = patient_name
    treatment = treatment
    summary = f"{setting}: {name} for {treatment}"
    
    start, end = convert_utc(timeobj, booking_duration)
    event = {
        'summary': summary, # this will be the intent tag on backend
        'location': 'Southend On Sea', # if room booking service is available write here/default loc
        'description': description,
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
    app_credentials = AppCredentials.objects.get(id=1)
    secret = app_credentials.google_secret
    client_secret_file = os.path.abspath('media/'+ str(secret))
    print(client_secret_file)
    credentials = Credentials.from_service_account_file(client_secret_file,scopes=scopes)
    try:
        service = build('calendar', 'v3', credentials=credentials)
        service.events().insert(calendarId=calendar_id, body=event).execute()
    except Exception as e:
        print(e)
    return None
    

def check_blank(text, session):
    treatments = session['mappings']['booking categories']
                    
    threshold = 0.65  # Adjust the threshold as needed

    # Remove whitespace and convert the input text to lowercase
    processed_text = text.strip().lower()

    # Calculate the Levenshtein distance between the target phrase and each substring
    for i in range(len(processed_text)):
        for j in range(i + 1, len(processed_text) + 1):
            substring = processed_text[i:j]
            for t in treatments:
                distance = levenshtein_distance(t, substring)
                similarity = 1 - (distance / max(len(treatments), len(substring)))
                
                # Check if the similarity exceeds the threshold
                if similarity >= threshold:
                    #print('Yes')
                    return t

    return False


def levenshtein_distance(s, t):
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s[i - 1] == t[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    return dp[m][n]
    

def extract_numbers(text):
    pattern = r'\b(\d+|[a-zA-Z]+)\b'
    matches = re.findall(pattern, text)
    numbers = []
    
    for match in matches:
        try:
            number = int(match)  # Try converting to integer
            numbers.append(number)
        except ValueError:
            try:
                number = w2n.word_to_num(match)  # Convert word-based numbers to integers
                numbers.append(number)
            except ValueError:
                continue  # Ignore if neither an integer nor a word-based number
    
    return numbers[0]

def timenow():
    from datetime import datetime
    import pytz
    london_timezone = pytz.timezone('Europe/London')
    current_datetime_london = datetime.now(london_timezone)
    formatted_datetime = current_datetime_london.strftime('%Y-%m-%dT%H:%M:%SZ')
    return formatted_datetime
