from utility.logger import setup_logger
import os
import logging
from pathlib import Path
from typing import List
import fitz
from utility.Exception import DeepFakeDetectionException as DFDException
import pdfplumber
from langchain_core.documents import Document


setup_logger()
logger = logging.getLogger(__name__)


def process_pdf(file_path: str) -> List[Document]:
    logger.info("Starting the processing of pdf")
    try:
        logger.debug("Getting File Path...")
        path = Path(file_path)

        if not path.is_file():
            raise DFDException(f"File not found at: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise DFDException(f"File is not of pdf format: {file_path}")

        output_dir = Path("extracted_images")
        output_dir.mkdir(exist_ok=True)

        documents = []

        
        pdf = fitz.open(path)

        for page_number, page in enumerate(pdf): # type: ignore
            logger.debug(f"Processing page number {page_number}")

            # Text
            text = page.get_text("text").strip()
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "type": "text",
                            "source": str(path),
                            "page_number": page_number + 1,
                        }
                    )
                )
                logger.debug(f"Appended text document for page {page_number + 1}")

          
            images = page.get_images(full=True)
            if images:
                for image_index, image in enumerate(images):
                    xref = image[0]
                    image_data = pdf.extract_image(xref)
                    image_bytes = image_data["image"]
                    image_ext = image_data["ext"]

                    image_name = (
                        f"page_{page_number + 1}"
                        f"_image_{image_index + 1}"
                        f".{image_ext}"
                    )
                    logger.debug(f"Image name here is: {image_name}")

                    image_path = output_dir / image_name
                    logger.debug(f"Image path here is: {image_path}")

                    image_path.write_bytes(image_bytes)

                    documents.append(
                        Document(
                            page_content="",
                            metadata={
                                "type": "image",
                                "source": str(path),
                                "page": page_number + 1,
                                "image_path": str(image_path)
                            }
                        )
                    )

        logger.info(f"Text and image processing of the pdf completed: {file_path}")
        pdf.close()

        # ---- Table extraction via pdfplumber ----
        logger.info("Starting table extraction")
        with pdfplumber.open(file_path) as plumber_pdf:
            for page_number, page in enumerate(plumber_pdf.pages):
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    rows = []
                    for row in table:
                        cleaned_row = [(cell or "").strip() for cell in row]
                        rows.append(cleaned_row)

                    if not rows:
                        continue

                    markdown = []
                    markdown.append("| " + " | ".join(rows[0]) + " |")
                    markdown.append("| " + " | ".join(["---"] * len(rows[0])) + " |")

                    for row in rows[1:]:
                        markdown.append("| " + " | ".join(row) + " |")

                    table_text = "\n".join(markdown)

                    documents.append(
                        Document(
                            page_content=table_text,
                            metadata={
                                "type": "table",
                                "source": str(path),
                                "page": page_number + 1
                            }
                        )
                    )

        logger.info(f"PDF processing completed. Created {len(documents)} documents.")
        return documents

    except Exception as error:
        logger.exception("Failed to process PDF")
        raise DFDException("Failed to process PDF") from error

    finally:
        logger.info("Exiting process_pdf")


if __name__ == "__main__":
    logger.info("Testing the pdf_loader here...")
    process_pdf(r"C:\Users\dell\OneDrive\Documents\LangChain\DeepfakeDetection\test\resume.pdf")