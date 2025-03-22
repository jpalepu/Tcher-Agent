import os
import streamlit as st
import tempfile
import time
import logging
from dotenv import load_dotenv
import json
# Add this to the imports section if not already there
import streamlit as st
from extractor import DocumentExtractor
from script_generator import ScriptGenerator
from audio_generator import AudioGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Document to Podcast Converter",
    page_icon="🎙️",
    layout="wide"
)

# Initialize components
@st.cache_resource
# Add this to the load_components function
def load_components():
    return {
        "extractor": DocumentExtractor(),
        "script_generator": ScriptGenerator(),
        "audio_generator": AudioGenerator()
    }

# Add this to the main UI section
# Add custom CSS at the top of the file
# Update the custom CSS section
st.markdown("""
<style>
    /* Dark mode base colors */
    body {
        color: #E0E0E0;
    }
    
    /* Main container styling */
    [data-testid="stAppViewContainer"] {
        background: #0E1117;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #1A1D24;
        border-right: 1px solid #2D3037;
        padding: 2rem;
    }
    
    /* Card styling */
    .custom-card {
        background: #1E293B;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #2D3037;
        margin: 1rem 0;
        color: #E0E0E0;
    }
    
    /* Button styling */
    .stButton>button {
        background: #6D28D9 !important;
        color: white !important;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(109,40,217,0.4);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #6D28D9 !important;
    }
    
    /* Text input styling */
    .stTextInput>div>div>input {
        color: #E0E0E0;
        background-color: #1A1D24;
    }
    
    /* Select box styling */
    .stSelectbox>div>div>select {
        background-color: #1A1D24;
        color: #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## 🎚️ Configuration")
        
        # Conversation type selection
        conversation_type = st.selectbox(
            "1. Conversation Style",
            ["Educational", "Interview", "Panel Discussion", "Storytelling"],
            index=0,
            help="Select the type of conversation format you want"
        )
        
        # Document type selection
        document_type = st.selectbox(
            "2. Document Type",
            ["Research Article", "Review Article", "Case Study"],
            index=0,
            help="Select the type of document you're uploading"
        )
        
        st.markdown("---")
        st.markdown("ℹ️ **About**  \nConvert documents to podcasts with AI-powered narration")

    # Main content area
    col1, col2 = st.columns([2, 3])
    
    # Get components
    components = load_components()
    extractor = components["extractor"]
    script_generator = components["script_generator"]
    audio_generator = components["audio_generator"]
    
    with col1:
        st.markdown("## 📤 Upload Document")
        
        with st.container(height=300):
            uploaded_file = st.file_uploader(
                "Drag and drop PDF here",
                type=["pdf"],
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                st.success("File uploaded successfully!")
                st.write(f"**File Name:** {uploaded_file.name}")
                st.write(f"**File Size:** {uploaded_file.size//1024} KB")

    with col2:
        st.markdown("## 🎧 Audio Generation")
        
        if uploaded_file:
            # Processing section
            if st.button("✨ Generate Podcast", use_container_width=True):
                with st.status("Processing Pipeline", expanded=True) as status:
                    try:
                        # Save temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_path = tmp_file.name
                        
                        # Processing steps with proper component references
                        st.write("🔍 Extracting text...")
                        document_data = components["extractor"].extract_text(
                            temp_path, 
                            document_type=document_type.lower().replace(" ", "_")
                        )
                        
                        st.write("📝 Generating script...")
                        script_json = components["script_generator"].generate_script(document_data)
                        
                        st.write("🔊 Synthesizing audio...")
                        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = os.path.join(output_dir, f"{uploaded_file.name.split('.')[0]}_podcast.mp3")
                        audio_path = components["audio_generator"].generate_podcast(script_json, output_path)
                        
                        status.update(label="Processing Complete!", state="complete")
                        
                        # Display results
                        st.balloons()
                        st.session_state.generated_audio = audio_path
                    
                    except Exception as e:
                        status.update(label="Processing Failed", state="error")
                        st.error(f"Error: {str(e)}")
                    
                    finally:
                        if 'temp_path' in locals():
                            os.unlink(temp_path)
            
            # Display results if audio exists in session state
            if 'generated_audio' in st.session_state:
                st.markdown("---")
                st.markdown("### 🎉 Your Podcast is Ready!")
                
                with st.container():
                    st.audio(st.session_state.generated_audio)
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.download_button(
                            label="📥 Download MP3",
                            data=open(st.session_state.generated_audio, "rb").read(),
                            file_name=os.path.basename(st.session_state.generated_audio),
                            mime="audio/mpeg",
                            use_container_width=True
                        )
                    with col_d2:
                        if st.button("🔄 Generate New", use_container_width=True):
                            st.session_state.clear()
                            st.rerun()
        else:
            # Update the empty state container
            with st.container(height=300):
                st.markdown("""
                <div style="text-align: center; padding: 4rem">
                    <div style="font-size: 4rem; color: #6D28D9">🎙️</div>
                    <h3 style="color: #E0E0E0">Upload a document to begin</h3>
                    <p style="color: #94A3B8">Supported formats: PDF</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()