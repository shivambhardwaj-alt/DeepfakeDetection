import logging
from utility.logger import setup_logger
from utility.Exception import DeepFakeDetectionException as DFDException
setup_logger()
logger = logging.getLogger(__name__)
def run_application():
    try : 
        if __name__ == '__main__':
            logger.info("Application Started Successfully")
        else:
            logger.error("Application failed !")
    except Exception as error : 
        logger.error("Application Starting Failed")
        raise DFDException("Application Starting failed" )
run_application()
