from sqlalchemy import create_engine 
import os 
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine , async_sessionmaker, create_async_engine , AsyncSession
from config import Config
import logging 
from utility.logger import setup_logger
from utility.Exception import DeepFakeDetectionException as DFDException
setup_logger()

logger = logging.getLogger(__name__)
engine = create_async_engine(
    Config.DATABASE_URL or "",
    echo = True  , 
    pool_size = 20 , 
    max_overflow = 20 , 
    pool_pre_ping = True
)


AsynSessionLocal = async_sessionmaker(
    bind = engine , 
    expire_on_commit = False, 
    class_ = AsyncSession
)


async def get_db():
    try : 
        logger.info("Creating database session....")
        async with AsyncSession() as session:
            logger.info("Database Session Created: " , session)
        yield session
        logger.info("Database session closed....")
    except:
        raise DFDException("Failed to create session") 
        

    