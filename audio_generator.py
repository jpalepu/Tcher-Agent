import os
import logging
import tempfile
from dotenv import load_dotenv
import torch
from pydub import AudioSegment
import langdetect

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Register safe globals (for PyTorch 2.6+)
try:
    from torch.serialization import add_safe_globals
    from TTS.config.shared_configs import BaseDatasetConfig
    add_safe_globals([BaseDatasetConfig])
    logger.info("Successfully registered TTS classes as safe globals")
except Exception as e:
    logger.warning(f"Failed to register TTS classes as safe globals: {e}")

# Import TTS
try:
    from TTS.api import TTS
except Exception as e:
    logger.error(f"Failed to import TTS: {e}")
    raise

class AudioGenerator:
    def __init__(self):
        logger.info("Initializing AudioGenerator")
        try:
            # Check for Apple Metal support first (for macOS devices)
            if torch.backends.mps.is_available():
                self.device = "mps"
                logger.info("Using Apple Metal (MPS) for acceleration")
            # Then check for CUDA support
            elif torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using CUDA for acceleration")
            else:
                self.device = "cpu"
                logger.info("Using CPU for processing (no GPU acceleration available)")

            # Configure CUDA if using it
            if self.device == "cuda":
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = True
                torch.cuda.empty_cache()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"GPU: {gpu_name} with {gpu_memory:.2f} GB memory")
            
            # Configure MPS if using it
            elif self.device == "mps":
                # No specific configuration needed for MPS, but we can log that we're using it
                logger.info("Apple Silicon GPU acceleration enabled")

            # Patch torch.load to set weights_only=False
            original_torch_load = torch.load
            def patched_torch_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_torch_load(*args, **kwargs)
            torch.load = patched_torch_load

            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

            torch.load = original_torch_load  # restore

            self.available_speakers = list(self.tts.synthesizer.tts_model.speaker_manager.speakers.keys())
            logger.info(f"Available speakers: {self.available_speakers}")

            # Create voice mappings
            self.voice_mappings = {
                "Host": {"voice": self.available_speakers[0], "language": "en"},
                "Guest": {"voice": self.available_speakers[1] if len(self.available_speakers) > 1 else self.available_speakers[0], "language": "en"},
                "Guest 1": {"voice": self.available_speakers[2] if len(self.available_speakers) > 2 else self.available_speakers[0], "language": "en"},
                "Guest 2": {"voice": self.available_speakers[3] if len(self.available_speakers) > 3 else self.available_speakers[0], "language": "en"},
            }

            logger.info(f"Voice mappings: {self.voice_mappings}")
            logger.info("TTS initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            raise

    def detect_language(self, text):
        try:
            detected = langdetect.detect(text)
            supported = {
                'en', 'fr', 'es', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl',
                'cs', 'ar', 'zh', 'ja', 'ko', 'hu'
            }
            return detected if detected in supported else 'en'
        except Exception as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to English.")
            return 'en'

    def generate_audio_segment(self, text, speaker_name, language=None):
        logger.info(f"Generating audio for {speaker_name}: {text[:50]}...")
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            if not language:
                language = self.detect_language(text)

            speaker_settings = self.voice_mappings.get(speaker_name)
            if not speaker_settings:
                logger.warning(f"Speaker '{speaker_name}' not recognized. Falling back to default.")
                speaker_settings = {"voice": self.available_speakers[0], "language": language}

            speaker_settings["language"] = language  # ensure consistency
            logger.info(f"Using speaker: {speaker_settings['voice']} | language: {language}")

            self.tts.tts_to_file(
                text=text,
                file_path=temp_path,
                speaker=speaker_settings["voice"],
                language=language
            )

            audio_segment = AudioSegment.from_wav(temp_path)
            os.unlink(temp_path)
            return audio_segment

        except Exception as e:
            logger.error(f"Error generating audio segment: {e}")
            raise

    def generate_podcast(self, script_json, output_path):
        logger.info(f"Generating podcast: '{script_json.get('title')}'")
        try:
            podcast = AudioSegment.silent(duration=500)
            all_text = " ".join([turn["text"] for turn in script_json.get("script", [])])
            script_language = self.detect_language(all_text)
            logger.info(f"Detected script language: {script_language}")

            for i, turn in enumerate(script_json.get("script", [])):
                speaker = turn["speaker"]
                text = turn["text"]

                if speaker not in self.voice_mappings:
                    logger.warning(f"Unknown speaker '{speaker}', defaulting to Host.")
                    speaker = "Host"

                logger.info(f"Turn {i+1}/{len(script_json['script'])} - {speaker}")
                segment = self.generate_audio_segment(text, speaker, language=script_language)
                podcast += AudioSegment.silent(duration=300)
                podcast += segment

            podcast += AudioSegment.silent(duration=1000)
            podcast.export(output_path, format="mp3", bitrate="192k")
            logger.info(f"Podcast generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating podcast: {e}")
            raise

# Example usage
if __name__ == "__main__":
    generator = AudioGenerator()
    sample_script = {
        "title": "Introduction to AI",
        "description": "A brief overview of artificial intelligence",
        "speakers": ["Host", "Guest"],
        "script": [
            {"speaker": "Host", "text": "Welcome to our podcast on Artificial Intelligence. Today we're exploring the basics of AI."},
            {"speaker": "Guest", "text": "Thanks for having me. AI is a fascinating field that's rapidly evolving."},
            {"speaker": "Host", "text": "Could you explain what exactly AI is?"},
            {"speaker": "Guest", "text": "Certainly! AI refers to systems that can perform tasks that typically require human intelligence."}
        ]
    }

    output_file = "sample_podcast.mp3"
    generator.generate_podcast(sample_script, output_file)
