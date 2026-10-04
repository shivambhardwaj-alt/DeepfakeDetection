import io
import logging
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

from PIL import Image, ImageOps, UnidentifiedImageError

from app.models.config_models import ImageProcessingModels
from utility.Exception import DeepFakeDetectionException as DFDException
from utility.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

AI_LABELS = {"fake", "deepfake", "ai", "artificial", "label_1"}
HUMAN_LABELS = {"real", "realism", "human", "label_0"}


class ImageProcessor:
    def __init__(self, max_workers: int = 4):
        self.image_clients = ImageProcessingModels().images_processing_clients
        self.max_workers = max_workers

    def load_image(self, source) -> Image.Image:
        """source can be raw bytes or a file path."""
        try:
            if isinstance(source, (bytes, bytearray)):
                opened = Image.open(io.BytesIO(source))
            else:
                opened = Image.open(source)

            with opened as img:
                img = ImageOps.exif_transpose(img)
                return img.convert("RGB")

        except FileNotFoundError as e:
            raise DFDException(f"File not found: {source}") from e
        except UnidentifiedImageError as e:
            raise DFDException("File is not a valid image") from e
        except Image.DecompressionBombError as e:
            raise DFDException("Image is too large to process") from e
        except OSError as e:
            raise DFDException(f"Could not read image: {e}") from e
        except TypeError as e:
            raise DFDException(f"Unsupported image source type: {type(source).__name__}") from e

    @staticmethod
    def to_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")     
        return buf.getvalue()

    def findConfidenceScore(self, model: str, image: bytes) -> float:
        """Probability (0-1) that the image is fake, according to one model."""
        try:
            client = self.image_clients[model]
            results = client.image_classification(image, model=model)
            logger.info(f"[{model}] raw output: {results}")

            labels = {str(r.label).strip().lower(): float(r.score) for r in results}

            for label, score in labels.items():
                if label in AI_LABELS:
                    return score
            for label, score in labels.items():
                if label in HUMAN_LABELS:
                    return 1.0 - score

            raise DFDException(f"Unknown labels from '{model}': {list(labels)}")

        except DFDException:
            raise
        except Exception as e:
            raise DFDException(f"Model '{model}' failed: {e}") from e

    def process_image(self, source) -> dict:
        img = self.load_image(source)            
        data = self.to_bytes(img)                

        scores: Dict[str, float] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self.findConfidenceScore, n, data): n
                       for n in self.image_clients}
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    scores[name] = fut.result()
                except Exception as e:
                    logger.error(f"Model '{name}' skipped: {e}")

        if not scores:
            raise DFDException("All image models failed")

        values = list(scores.values())
        confidence = statistics.mean(values)
        spread = max(values) - min(values)

        if spread > 0.5:
            verdict = "uncertain"
        elif confidence >= 0.65:
            verdict = "likely_fake"
        elif confidence <= 0.35:
            verdict = "likely_real"
        else:
            verdict = "uncertain"

        return {
            "verdict": verdict,
            "confidence": round(confidence, 3),
            "model_disagreement": round(spread, 3),
            "model_scores": {k: round(v, 3) for k, v in scores.items()},
        }


if __name__ == "__main__":
    ic = ImageProcessor()
    print(ic.process_image(r"C:\Users\dell\OneDrive\Documents\LangChain\DeepfakeDetection\test\demo.jpeg"))