from django.test import TestCase
from .celeryfuncs import cache_chat_message
from .extract import get_response
from aurora_api.models import Customer, Models, AppCredentials
from aurora_api.sessionsmanager import SessionManager

class YourTestCase(TestCase):
    def setUp(self):
        # Create a Customer object for testing
        self.customer = Customer.objects.create(
            name="Southend Council",
            calendar_id="biokporsolomon@southend.gov.uk",
            origin="https://262e5fa0c08646e6871bedd3d249507d.vfs.cloud9.eu-west-2.amazonaws.com",
            mappings={"booking categories": ["general dentistry", "dental hygiene", "dermal fillers", "wrinkle treatment", "teeth straightening", "teeth whitening"]},
            phone_number="07989462527",
            email="biokporsolomon@yahoo.co.uk",
            closing={"greeting": 1, "child registration process": 2}
        )
        print(f"Stage 1: Customer object created")
        
        self.model = Models.objects.create(
            customer_name = self.customer,
            intent = {
                    "entries": [
                        {
                          "id": 1,
                          "name": "Entry 1",
                          "description": "This is the first entry in the JSON project."
                        },
                        {
                          "id": 2,
                          "name": "Entry 2",
                          "description": "This is the second entry in the JSON project."
                        }
                    ]},
            training_file = None,
            model_key = None
            )
        print(f"Stage 2: Model object created")
        
        self.credentials = AppCredentials.objects.create(
            google_secret = None,
            platform = 'Google'
            )

    def test_main_components(self):
        # Replace 'http://example.com' with your actual origin
        origin = "https://262e5fa0c08646e6871bedd3d249507d.vfs.cloud9.eu-west-2.amazonaws.com"
            
        # Instantiate SessionManager
        session_manager = SessionManager(origin)
            
        # Call create_session
        session = session_manager.create_session()
        msg = 'Hi'
       
        # Assert that the session is created successfully
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.session_key)
        self.assertEqual(session['origin'], origin)
        print(f"Stage 3: Session created succesfully !!")
        try:
            session['session_key'] = session.session_key
            session.save()
            output = get_response(msg, session)
            print(output)
            #print(f"Stage 4: Agent Connection Passed")
            
            #cache_chat_message(session.session_key, msg, output, False)
            #print(f"Stage 5: Caching mechanism Passed")
            
        except Exception as e:
            print(e)
    
        
            
            

