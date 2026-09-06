import logging 
from utility.logger import setup_logger
from utility.Exception import DeepFakeDetectionException as DFDException 
from models.config_models import TextModels

class TextProcessingChain:
    def __init__(self):
        self.models = TextModels().get_models()
        self.clients = TextModels().get_clients()
        self.explainer = None 
        
        # I will the confidence score from the all the models here and then explainer will explain why is that in a defined format 
        def run_chain(self , text : str ):
            
            
        
        
        

