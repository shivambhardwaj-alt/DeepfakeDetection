import logging
from utility.Exception import DeepFakeDetectionException as DFDException 
from utility.logger import setup_logger
from pathlib import Path 
from docx import Document as DocxDocument
from zipfile import ZipFile
from docx.table import Table
from docx.text.paragraph import Paragraph
from langchain_core.documents import Document
from typing import Optional , List
import os 
setup_logger()

logger =  logging.getLogger(__name__)

#yeilding one by one each and every paragraph , tables and images here 
def iter_block_items(parent):
    try : 
        logger.info("Starting iteration in docx body")
        
        parent_element = parent.element.body
        for child in parent_element.iterchildren():
            if child.tag.endswith("}p"):
                yield Paragraph(child, parent)
            elif child.tag.endswith("}tbl"):
                yield Table(child, parent)
        logger.info("Iteration Finished here of Docx body")
    except: 
        raise DFDException("Failed to iterate the body of the docx in docx_loader")
    


# now processing the docx file here
    
def process_docx(file_path : str) -> List[Document]:
    logger.info("In the process_docx file ")
    try: 
        if not Path(file_path).is_file():
            raise DFDException(f"DOCX file not found: {file_path}")

        path = Path(file_path)
        doc = DocxDocument(file_path)
        if not doc : 
            raise DFDException(f'Document file is not found : {file_path}')
        output_dirs = os.makedirs("extracted_images" , exist_ok= True)
        documents = []
        logger.info("Opening docx file here")
        with ZipFile(file_path , "r") as zipfile :
            logger.info(f"Opened file here {file_path}")
            image_files  =  {}
            logger.info("Processing Images here >>>>>>")
            for name in zipfile.namelist():
                if name.startswith("word/media/"):
                    image_name = Path(name).name
                    image_path = f'{output_dirs}/{image_name}'
                    
                    with zipfile.open(name) as image:
                        image_path.write_bytes(image.read()) # type: ignore # most important line for me new line  it will write bytes of images into file path
                    image_files[image] = image_path
            logger.info("Writing of images has been successful ")                        
            logger.info("Now heading towards the processinf of text here")
            for element in iter_block_items(doc):
                if isinstance(element , Paragraph):
                    text = element.text.strip()
                    if text : 
                        documents.append(
                            Document(page_content = text, meta_data = {"type" : "paragraph" , "source" : file_path})
                        
                        )
                        # now if paragraph contains images here 
                        for run in element.runs:  # will process run tag in document loader here
                            drawings = run._element.xpath( ".//*[local-name()='drawing']")
                            for drawing in drawings:

                                    blips = drawing.xpath(
                                        ".//*[local-name()='blip']"
                                    )

                                    for blip in blips:

                                        embed = blip.get(
                                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                                        )

                                        if embed:
                                            image_part = doc.part.related_parts[embed]

                                            image_name = Path(
                                                image_part.partname
                                            ).name

                                            image_path = f'{output_dirs} / {image_name}'

                                            image_path.write_bytes( # type: ignore
                                                image_part.blob
                                            )

                                            documents.append(
                                                Document(
                                                    page_content="",
                                                    metadata={
                                                        "type": "image",
                                                        "source": str(file_path),
                                                        "image_path": str(image_path)
                                                    }
                                                )
                                            )
                #now do it for the table here 
                    logger.debug("Processing of current is going on .....")
                
                elif isinstance(element, Table):
                    rows =  []
                    for row in element.rows:
                        cells =  []
                        for cell in row.cells:
                            cells.append(cell.text.strip().replace("\n" , " "))
                        rows.append(cell)
                    if rows:

                        markdown = []

                        markdown.append(
                            "| " + " | ".join(rows[0]) + " |"
                        )

                        markdown.append(
                            "| " + " | ".join(["---"] * len(rows[0])) + " |"
                        )

                        for row in rows[1:]:

                            markdown.append(
                                "| " + " | ".join(row) + " |"
                            )

                        table_text = "\n".join(markdown)

                        documents.append(
                            Document(
                                page_content=table_text,
                                metadata={
                                    "type": "table",
                                    "source": str(file_path)
                                }
                            )
                        )
        logger.info("Processing finished here")
        return documents
    except Exception as error : 
        raise DFDException("Failed to process DocxFile in process_docx func_")
    finally:
        logger.info("Out of the process_docx-function")
        
            
            
            
        return documents
if __name__ == "__main__":
    process_docx(
        r"C:\Users\dell\OneDrive\Documents\LangChain\DeepfakeDetection\test\Shivam_Bhardwaj_Cover_Letter.docx"
    )            
        

    
                