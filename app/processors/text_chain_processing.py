import logging 
import os 
import statistics
import re
from concurrent.futures import ThreadPoolExecutor , as_completed 
from langchain.chat_models import init_chat_model
from app.models.config_models import TextModels
from app.prompts.textProcessingPrompt import text_prompt , Verdict 
from utility.Exception import DeepFakeDetectionException as DFDException 
from utility.logger import setup_logger
from typing import List, Dict, Optional , Any 
from app.models.config_models import ReasoningModel
logger = logging.getLogger(__name__)


SHORT_TEXT_WORDS = 30 
MAX_DISAGREEMENT = 0.5 
AI_THRESHOLD = 0.65
HUMAN_THRESHOLD =0.35
AI_LABELS = {"ai", "fake", "generated", "ai-generated", "ai_generated", "machine",
             "synthetic", "label_1", "1", "chatgpt", "llm"}
HUMAN_LABELS = {"human", "real", "human-written", "human_written", "original",
                "label_0", "0"}
MODEL_AI_LABEL: Dict[str, str] = {}


AI_PHRASES = [
    "it is important to note", "it is worth noting", "plays a crucial role",
    "play a crucial role", "in conclusion", "in summary", "furthermore",
    "moreover", "delve", "in today's fast-paced", "a testament to",
    "cannot be overstated", "ever-evolving", "navigate the complexities",
    "tapestry", "rich landscape", "numerous benefits", "various industries",
    "it is essential to", "overall,",
]


CONTRACTION_RE = re.compile(r"\b\w+'(?:t|s|re|ve|ll|d|m)\b", re.I)
FIRST_PERSON_RE = re.compile(r"\b(i|me|my|mine|myself|we|our)\b", re.I)




class TextProcessing: 
    def __init__(self , useExplainer : bool = False ,max_workers:int = 4 ):
        text_models = TextModels()
        self.models = text_models.get_models()
        self.clients = text_models.get_clients()
        self.max_workers =  max_workers
        self.useExplainer = useExplainer 
        self.chat_client = None 
    def singleModelScore(self, name : str , data : str):
        try : 
            logger.info(f"Getting the result {name} model... ")
            client = self.clients[name]
            results  =  client.text_classification(data, model = name , top_k = 5)
            logger.info(f"f[{name}]  raw output : {results}")
            labels = {str(r.label).strip().lower(): float(r.score) for r in results}
            print(f"Labels are : '  {labels}")
            override = MODEL_AI_LABEL.get(name)
            # print(override)
            """this line is still needed to understand here i have no idea what is going on here"""
            if override and override.lower() in labels:
                return labels[override.lower()]
            for label, score  in labels.items():
                if label in AI_LABELS:
                    return score 
            for label, score in labels.items():
                if label in HUMAN_LABELS:
                    return 1.0 - score
            logger.warning(f'[{name}] unknown labels {list(labels)}; add them into AI_LABELS/HUMAN_LABELS ')
            raise DFDException(f"Unrecognised labels from '{name} : {list(labels)}'")
                
        except:
            logger.error(f'Model name {name}  is not working got error')
            raise DFDException(f"Error happened for model : {name}")
    def findConfidenceScore(self, data : str) -> Dict[str ,float]:
        if not isinstance (data, str) or not data.strip():
            raise DFDException("Input text must be a non-empty string")
        scores : Dict[str, float] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers)  as pool:
            futures  = {pool.submit(self.singleModelScore , n , data) : n for n in self.clients}
            for fut in as_completed(futures):
                name = futures[fut]
                try :
                    scores[name]  = fut.result() 
                except Exception as e : 
                    logger.error(f"Model {name} failed to give output here...")
            logger.info(f"Scores are >>>> {scores}")
        return scores
    @staticmethod 
    def _text_signals(data : str) -> Dict[str, Any]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", data.strip()) if s.strip()]
        words  = re.findall(r"\b[\w']+\b", data)
        lengths = [len(re.findall(r"\b[\w']+\b", s)) for s in sentences] or [0]
        lowered = data.lower()
        ai_hits : List[str] = []
        for phrase in AI_PHRASES:
            idx = lowered.find(phrase)
            if idx != -1:
                ai_hits.append(data[idx : idx + len(phrase)]) 
               
        
        return {
            "n_words": len(words),
            "n_sentences": len(sentences),
            "avg_len": statistics.mean(lengths),
            "len_std": statistics.pstdev(lengths) if len(lengths) > 1 else 0.0,
            "ttr": (len({w.lower() for w in words}) / len(words)) if words else 0.0,
            "ai_phrases": ai_hits,
            "contractions": len(CONTRACTION_RE.findall(data)),
            "first_person": len(FIRST_PERSON_RE.findall(data)),
            "digits": len(re.findall(r"\d", data)),
            "informal": bool(re.search(r"(!{1,}|\.{3}|\b(lol|haha|btw|idk|tbh|gonna|wanna)\b)", data, re.I)),
        }
    def _rule_based_explain(self, data : str, score) :
        """ This method will explain here on the basis of result after getting confidence score and everything """
        try :
            reasoning = ReasoningModel()
            llm  = reasoning.reasoning_llm
            resultForSignals = self._text_signals(data)
          
            prompt = text_prompt.invoke({
                "data" : data , 
                "score" : score
            })
            
            structured_llm = llm.with_structured_output(Verdict)
            final_result = structured_llm.invoke(prompt)
            logger.info(f"finally got the result in the structured format :{final_result}")      
            return final_result 
            
        except: 
            raise DFDException("Failed in the process of making reasoning with reasoning model")

    