from app.processors.text_chain_processing import TextProcessing
import logging 
from utility.Exception import DeepFakeDetectionException as DFDException
from utility.logger import setup_logger
logger =  logging.getLogger(__name__)
setup_logger()
class TextProcessingChain:
    def __init__(self):
        self.result = None
        self.final_result = None
        self.processor = TextProcessing()
    def predict(self, data : str , isExplainer : bool = True):
        try : 
            self.result =  self.processor.findConfidenceScore(data)
            logger.info(f"Found the Confidence Score here : {self.result}")
            if isExplainer:
                logger.info("Explainer is ON ..")
                self.final_result = self.processor._rule_based_explain(data, self.result)
                logger.info("Found the final _result here...")
            return (self.result , self.final_result)
        except:
            raise DFDException("Failed to predict here ....")            
if __name__ == "__main__":
    t = TextProcessingChain()
    result , final_result  = t.predict("Hi this is shivam Bhardwaj")
    print("result is here " ,  result)
    print("final result is here " , final_result )
        
    
