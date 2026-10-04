from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel 
import logging 
from utility.logger import setup_logger
from utility.Exception import DeepFakeDetectionException as DFDException
from database.database import engine , get_db
setup_logger()

logger = logging.getLogger(__name__)
@asynccontextmanager
async def life_span(app:FastAPI):
        try : 
            logger.info("Server is running ....")
            logger.info("Creating Tables ")
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            yield 
            logger.info("Server has been stopped...")
        except:
            raise DFDException("Starting of server has been failed here")
                
        

version = "v1"
app =  FastAPI(
    version  = version, 
    title = "DeepFake Detection Api",
    lifespan=None , 
    description= "A REST API FOR THE DEEPFAKE MULTIMODAL DETECTION HERE"
)