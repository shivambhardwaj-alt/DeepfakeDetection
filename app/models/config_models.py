
from pydantic_settings import BaseSettings, SettingsConfigDict
from huggingface_hub import login
import json
from utility.logger import setup_logger
from huggingface_hub import InferenceClient
import logging
from pathlib import Path
from langchain_groq import ChatGroq
setup_logger()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    huggingface_token: str
    GROQ_API_KEY : str 
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
        pass
    def load_reasoning_model(self):
        base_dir = Path(__file__).resolve().parent
        model_file = f'{base_dir}/models.json'
        with open(model_file , 'r' , encoding= 'utf-8') as file:
            data = json.load(file)
            

