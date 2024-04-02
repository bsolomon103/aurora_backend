from google.cloud import translate_v2 as translate
import os
from django.conf import settings

def translate_to_eng(input_text, target='en'):
  key_path = os.path.join(settings.BASE_DIR, 'media', 'secrets_file', 'Google.json')
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
  #Initialize the client
  client = translate.Client()

  #Text to translate
  language = client.detect_language(input_text)
  
  if language['language'] is not 'en':
      translation = client.translate(input_text, target_language=target)
      return language['language'], translation['translatedText']
  return language['language'], input_text
  
  

def translate_from_eng(input_text, target=None):
    if target is not None:
        try:
            client = translate.Client()
            translation = client.translate(input_text, target_language=target)
            return translation['translatedText']
        except:
            print('Translation failed')
    else:
        return input_text
    