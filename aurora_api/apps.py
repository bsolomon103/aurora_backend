from django.apps import AppConfig
from .utils import create_vector_store

class AuroraApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aurora_api'
    
    def ready(self):
        # Load the vector store during application startup
        global vector_store
        vector_store = create_vector_store("tue21.pdf", "Southend_Council")
        
    
