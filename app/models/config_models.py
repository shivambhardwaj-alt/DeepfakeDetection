
from pydantic_settings import BaseSettings, SettingsConfigDict 
from pydantic import Field
from huggingface_hub import login
import json
from typing import List
import os
from utility.logger import setup_logger
from huggingface_hub import InferenceClient
import logging
from pathlib import Path
from langchain_groq import ChatGroq
from utility.Exception import DeepFakeDetectionException as DFDException
setup_logger()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    huggingface_token: str
    GROQ_API_KEY: str = Field(..., alias="GROQ_API_KEY")
    REASONING_MODEL_TEMPERATURE: float  = 0.6
    
    REASONING_MAX_RETRIES:int  = 2
    
    
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings() # type: ignore
login(token=settings.huggingface_token)

logger.info("Successfully authenticated with Hugging Face")

class TextModels : 
    def __init__(self):
        self.models = self._load_models()
        self.clients = self._make_clients()
    def _load_models(self):
        base_dir = Path(__file__).resolve().parent
        model_file = f'{base_dir}/models.json'
        result_models = []
        with open(model_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            for model in data['models']:
                if model['recommended']:
                    result_models.append(model)
        logging.info("Models successfully fetched from json file")
        return result_models
    def _make_clients(self):
        clients = {}
        for model in self.models : 
            model_name = model['name']
            clients[model_name] = InferenceClient(
                model=model_name
            )
            logger.info(
                "Created Hugging Face client for: %s",
                model_name
            )
        logging.info("Created clients successfully")
        return clients
    def get_models(self):
        return self.models
    def get_clients(self):
        return self.clients
class ReasoningModel:
    def __init__(self):
        self.reasoning_model_name = self.load_reasoning_model()
        self.reasoning_llm = self.create_reasoning_llm()
    def load_reasoning_model(self):
        try :
            base_dir = Path(__file__).resolve().parent
            model_file = f'{base_dir}/models.json'
            with open(model_file , 'r' , encoding= 'utf-8') as file:
                data = json.load(file)
                curr_reasoning_model_info = data["ReasoningModels"]
                logger.info(f'Model which is going to use in reasoning info : {curr_reasoning_model_info}')
                return curr_reasoning_model_info[0]['name']
        except :
            raise DFDException("Failed to load reasoning model here....")
    def create_reasoning_llm(self):
        if settings.GROQ_API_KEY : 
            
            reasoning_llm = ChatGroq(model = self.reasoning_model_name , api_key= settings.GROQ_API_KEY, temperature  = settings.REASONING_MODEL_TEMPERATURE ,max_retries=settings.REASONING_MAX_RETRIES )
            logger.info("Creation of reasoning llm has been succesful here")
            return reasoning_llm
    
        else:
            raise DFDException("Can't get reasoning model because API_KEY_ is absent")
        

        
            
            

class ImageProcessingModels:
    """This will give all models of Images in a list and clients are being provided in Images processing """
    def __init__(self):
        self.images_processing_models : List[str] = self.get_video_models()
        self.images_processing_clients  = self.get_video_clients()
    def get_video_models(self) -> List[str]:
        try:
            logger.info("Starting to load the image models here .....")
            base_dir  = Path(__file__).resolve().parent
            model_file = f'{base_dir}/models.json'
            res : List[str] = []
            with open(model_file, "r" , encoding =  "utf-8") as file : 
                data = json.load(file)
                if not data : 
                    logger.info("No data has been found file")
                models = data["ImageProcessingModels"]
                for obj in models:
                    res.append(obj["name"])
                    logger.debug(f"Loading current models is : {obj}")
            logger.info("Loading of the images processing models has been completed and now ready to use ...")                
            return res                        
        except FileNotFoundError as e : 
            raise DFDException(f'File is not found with this {model_file}  path') from e 
        except json.JSONDecodeError as e : 
            raise DFDException(f'Model Config is not valid json here ..') from e 
        except OSError as e :
            raise DFDException(f'Could not read model config {e}') from e 
        except:
            raise DFDException("[Error]: Can't load the video_models here..")
    def get_video_clients(self):
        try :
            logger.info("Starting to make clients for the Image processing models for the deepfake detection..")
            clients = {}
            for model in self.images_processing_models:
                clients[model] = InferenceClient(model = model)
                if not clients:
                    logger.debug(f'Getting client for  this models is failed here .. {model}')
            logger.info("Getting models has been successful here...")
            return clients
        except Exception as e :
            raise DFDException(f"Failed to make the clients for the Image processing models here .. => {e} ")
            

