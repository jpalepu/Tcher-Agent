import os
import logging
from dotenv import load_dotenv
import json
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScriptGenerator:
    """Class to generate podcast scripts from document text using Azure OpenAI."""

    def __init__(self):
        logger.info("Initializing ScriptGenerator")
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("OPENAI_API_BASE")
            )
            self.deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
            logger.info(f"Using deployment: {self.deployment_name}")
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

    def generate_script(self, document_data, num_speakers=2, max_length=4000):
        """
        Generate a podcast script based on document text and document type.
        
        Args:
            document_data: Dictionary containing text and document type information
            num_speakers: Number of speakers in the podcast
            max_length: Maximum length of document text to process
        """
        document_text = document_data.get("text", "")
        document_type = document_data.get("document_type", "research_article")
        document_info = document_data.get("document_info", {})
        
        script_style = document_info.get("script_style", "analytical")
        document_name = document_info.get("name", "Research Article")
        
        logger.info(f"Generating script for {document_name} in {script_style} style")

        if len(document_text) > max_length:
            logger.info(f"Document text truncated from {len(document_text)} to {max_length} characters")
            document_text = document_text[:max_length]

        # Create a system prompt based on the document type
        system_prompt = self._get_system_prompt_for_document_type(
            document_type, 
            script_style, 
            num_speakers
        )

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the document content:\n\n{document_text}"}
                ],
                temperature=0.7,
                max_tokens=2000  # Adjust depending on Azure limits
            )

            content = response.choices[0].message.content
            script_json = json.loads(content)
            logger.info(f"Script generated successfully with {len(script_json['script'])} dialogue turns")
            return script_json

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise
    
    def _get_system_prompt_for_document_type(self, document_type, script_style, num_speakers):
        """Generate a system prompt based on the document type."""
        
        # Base prompt structure
        base_prompt = f"""
        You are an expert podcast script writer. Create a {script_style} podcast script based on the document content provided.
        The podcast should have {num_speakers} speakers named Host and Guest{' 1' if num_speakers > 2 else ''}{', Guest 2' if num_speakers > 3 else ''}.

        Format the script as a JSON object with the following structure:
        {{
            "title": "Podcast title based on the document",
            "description": "Brief description of the podcast",
            "speakers": ["Host", "Guest"{', "Guest 1"' if num_speakers > 2 else ''}{', "Guest 2"' if num_speakers > 3 else ''}],
            "script": [
                {{"speaker": "Host", "text": "Welcome to our podcast..."}},
                {{"speaker": "Guest", "text": "Thank you for having me..."}}
            ]
        }}
        """
        
        # Add document-type specific instructions
        if document_type == "research_article":
            specific_instructions = """
            This is a RESEARCH ARTICLE. Your script should be:
            - Analytical and detailed in discussing the research methods, results, and implications
            - Technical when explaining formulas, methodologies, and statistical analyses
            - Structured to cover the introduction, methods, results, and discussion sections
            - Longer and more in-depth, with detailed explanations of complex concepts
            - Include segments where speakers discuss limitations and future research directions
            
            Make the host ask probing questions about the research methodology and findings.
            Have the guest(s) explain technical concepts in a way that's accurate but accessible.
            """
        
        elif document_type == "review_article":
            specific_instructions = """
            This is a REVIEW ARTICLE. Your script should be:
            - Focused on synthesizing and comparing multiple research studies
            - Include critical analysis of the existing literature
            - Highlight consensus views and areas of disagreement in the field
            - Discuss the evolution of ideas and methodologies over time
            - Identify gaps in current knowledge and future research directions
            
            Make the host ask questions that compare different approaches or findings.
            Have the guest(s) provide balanced perspectives on the strengths and weaknesses of different studies.
            """
        
        elif document_type == "case_study":
            specific_instructions = """
            This is a CASE STUDY. Your script should be:
            - Conversational and narrative-driven, focusing on the specific case
            - Structured to tell the story of the case chronologically
            - Include detailed discussion of the context, challenges, interventions, and outcomes
            - Draw broader lessons and implications from the specific example
            - More informal and engaging, with personal perspectives
            
            Make the host ask questions about the specific decisions and turning points in the case.
            Have the guest(s) share insights about what made this case unique or representative.
            """
        
        else:  # Default case
            specific_instructions = """
            Make the conversation sound natural, engaging, and informative. Include:
            1. An introduction where the host welcomes the audience and introduces the topic
            2. A discussion of the main points from the document
            3. Questions and answers between speakers to explore the content
            4. A conclusion summarizing key takeaways
            """
        
        # Combine base prompt with specific instructions
        full_prompt = base_prompt + specific_instructions
        
        return full_prompt

# Example usage
if __name__ == "__main__":
    generator = ScriptGenerator()
    sample_text = """
    Artificial Intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. 
    AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
    """
    
    # Create a sample document data structure
    sample_document_data = {
        "text": sample_text,
        "document_type": "research_article",
        "document_info": {
            "name": "Research Article",
            "script_style": "analytical"
        }
    }
    
    script_json = generator.generate_script(sample_document_data)
    print(json.dumps(script_json, indent=2))
