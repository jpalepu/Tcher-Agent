import os
import logging
import tempfile
import json
import datetime
from dotenv import load_dotenv
from mistralai import Mistral
import base64
from PIL import Image
import io
import PyPDF2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get Mistral API key from environment variable
mistral_api_key = os.getenv('MISTRAL_API_KEY')
if not mistral_api_key:
    logger.error("MISTRAL_API_KEY not found in environment variables")
    raise ValueError("MISTRAL_API_KEY is required")

class DocumentExtractor:
    """Class to handle document text extraction using Mistral AI OCR."""
    
    def __init__(self):
        logger.info("Initializing DocumentExtractor with Mistral AI")
        self.client = Mistral(api_key=mistral_api_key)
        self.model = "mistral-ocr-latest"
        # Create debug directory if it doesn't exist
        self.debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output")
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Define document types and their characteristics
        self.document_types = {
            "research_article": {
                "name": "Research Article",
                "description": "Original research with methods, results, and analysis",
                "script_style": "analytical"
            },
            "review_article": {
                "name": "Review Article",
                "description": "Summarizes and synthesizes existing research on a topic",
                "script_style": "explanatory"
            },
            "case_study": {
                "name": "Case Study",
                "description": "In-depth analysis of a specific instance or example",
                "script_style": "conversational"
            }
        }
    
    def _save_debug_json(self, file_path, text):
        """Save extracted text to a JSON file for debugging."""
        try:
            # Create a debug filename based on the original filename
            base_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(base_name)[0]
            debug_file = os.path.join(self.debug_dir, f"{name_without_ext}_extracted.json")
            
            # Save the text along with metadata
            debug_data = {
                "source_file": file_path,
                "extraction_time": str(datetime.datetime.now()),
                "extracted_text": text,
                "text_length": len(text)
            }
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved debug output to {debug_file}")
            return debug_file
        except Exception as e:
            logger.error(f"Error saving debug JSON: {e}")
            return None
    
    def _encode_image_to_base64(self, image_path):
        """Convert an image file to base64 encoding."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file using Mistral OCR."""
        logger.info(f"Extracting text from PDF using Mistral OCR: {pdf_path}")
        try:
            # First try to extract text directly using PyPDF2
            text = ""
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n\n"
                
                if text.strip():
                    logger.info("Successfully extracted text from PDF using PyPDF2")
                    return text
                else:
                    logger.info("No text extracted from PDF using PyPDF2, trying OCR")
            except Exception as pdf_error:
                logger.warning(f"Error extracting text with PyPDF2: {pdf_error}")
            
            # If PyPDF2 fails or returns empty text, try using Mistral's document_url approach
            if pdf_path.startswith(('http://', 'https://')):
                # It's a URL
                ocr_response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "document_url",
                        "document_url": pdf_path
                    }
                )
                return ocr_response.text
            else:
                # For local files, we need to convert to images and process each page
                logger.info("Processing local PDF by converting to images")
                
                # Import pdf2image here to avoid dependency issues if not installed
                try:
                    from pdf2image import convert_from_path
                    
                    # Create a temporary directory to store images
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Convert PDF to images
                        images = convert_from_path(pdf_path)
                        
                        # Process each image and combine the results
                        all_text = []
                        for i, image in enumerate(images):
                            # Save the image to a temporary file
                            temp_image_path = os.path.join(temp_dir, f"page_{i}.jpg")
                            image.save(temp_image_path, "JPEG")
                            
                            # Extract text from the image
                            logger.info(f"Processing page {i+1}/{len(images)}")
                            page_text = self.extract_text_from_image(temp_image_path)
                            all_text.append(page_text)
                        
                        # Combine all text
                        return "\n\n".join(all_text)
                
                except ImportError:
                    logger.warning("pdf2image not installed, falling back to simple text extraction")
                    return "PDF extraction requires pdf2image library. Please install it or provide a URL to the PDF."
                except Exception as e:
                    logger.error(f"Error processing PDF as images: {e}")
                    return f"Error extracting text from PDF: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF with Mistral OCR: {e}")
            return f"Failed to extract text from PDF: {str(e)}"
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image file using Mistral OCR."""
        logger.info(f"Extracting text from image using Mistral OCR: {image_path}")
        try:
            # For images, use the correct format based on whether it's a URL or local file
            if image_path.startswith(('http://', 'https://')):
                # It's a URL
                ocr_response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "image_url",
                        "image_url": image_path
                    }
                )
            else:
                # For local files, encode to base64
                base64_image = self._encode_image_to_base64(image_path)
                
                # Process image with Mistral OCR using the correct format
                ocr_response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                )
            
            # Extract the text from the response
            return ocr_response.text
            
        except Exception as e:
            logger.error(f"Error extracting text from image with Mistral OCR: {e}")
            raise
    
    def extract_text(self, file_path, document_type="research_article"):
        """Extract text from a document (PDF or image) with document type context."""
        logger.info(f"Extracting text from file using Mistral OCR: {file_path}")
        logger.info(f"Document type: {document_type}")
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            text = self.extract_text_from_image(file_path)
        else:
            error_msg = f"Unsupported file format: {ext}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Save the extracted text to a JSON file for debugging
        debug_file = self._save_debug_json(file_path, text)
        
        # Return the extracted text along with document type information
        return {
            "text": text,
            "document_type": document_type,
            "document_info": self.document_types.get(document_type, self.document_types["research_article"]),
            "debug_file": debug_file
        }
    
    def get_document_types(self):
        """Return the available document types."""
        return self.document_types

# Example usage
if __name__ == "__main__":
    import datetime  # Import datetime for timestamp
    
    extractor = DocumentExtractor()
    # Replace with your test document path
    sample_path = "sample_document.pdf"
    if os.path.exists(sample_path):
        # Test with a specific document type
        result = extractor.extract_text(sample_path, document_type="review_article")
        print(f"Document type: {result['document_info']['name']}")
        print(f"Script style: {result['document_info']['script_style']}")
        print(f"Extracted text (first 500 chars): {result['text'][:500]}...")
    else:
        print(f"Sample file {sample_path} not found.")