# 🎙️ Tcher – Document to Podcast Converter

**Tcher** transforms documents into engaging, podcast-style audio. It extracts text from PDFs or images, generates conversational scripts using Azure OpenAI, and converts those scripts into natural-sounding audio using Coqui TTS.

## 🚀 Features

- 📄 Extracts text from **PDFs** and **image files**
- 🧠 Generates **conversational podcast scripts** with multiple speakers
- 🔊 Produces **natural-sounding audio** using multilingual voices
- 🌐 Simple and responsive **Streamlit web interface**
- 🎧 Optional **multi-speaker mapping and voice customization**

## ⚙️ Prerequisites

- Python **3.8+**
- OS: Windows, macOS, or Linux
- **CUDA-compatible GPU** (recommended for faster TTS generation)
- Azure OpenAI account with deployment set up
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) (for local PDF processing)

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/jpalepu/tcher.git
cd tcher
```

### 2. Create a virtual environment

```bash
python -m venv tcher-env
```

### 3. Activate the virtual environment

**Windows:**
```bash
tcher-env\Scripts\activate
```

**macOS/Linux:**
```bash
source tcher-env/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. For PDF processing with images, install Poppler

- **Windows:** Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH
- **macOS:** `brew install poppler`
- **Linux:** `apt-get install poppler-utils`

### 6. Create a `.env` file in the project root

See Environment Variables section below.

### 7. Run the application

```bash
streamlit run app.py
```

## 🔑 Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Azure OpenAI API Configuration
OPENAI_API_KEY=your_azure_api_key
OPENAI_API_VERSION=2023-05-15
OPENAI_API_BASE=https://your-resource-name.openai.azure.com/
OPENAI_DEPLOYMENT_NAME=your_deployment_name
```

## 🧩 How It Works

1. **Document Upload:** Upload PDFs or images containing text.
2. **Text Extraction:** The app extracts text using OCR for images and PDF parsing tools.
3. **Script Generation:** Azure OpenAI transforms content into conversational scripts.
4. **Audio Synthesis:** Coqui TTS converts scripts into natural-sounding audio.
5. **Download:** Get your podcast-ready audio file!

## 🖥️ Usage

1. Launch the app with `streamlit run app.py`
2. Upload your document (PDF or image)
3. Configure voice options if desired
4. Click "Generate Podcast" and wait for processing
5. Download your audio file when ready

## 🙋 FAQ

**Q: What file formats are supported?**  
A: Currently, Tcher supports PDF documents and common image formats (PNG, JPG, JPEG).

**Q: How long does processing take?**  
A: Processing time depends on document length, complexity, and your hardware. A 5-page document typically takes 2-5 minutes.

**Q: Can I customize the voices?**  
A: Yes! You can select from several pre-configured voices or upload custom voice samples.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request



[🎧 Listen to the generated podcast](sample_podcast.mp3)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ by [JPalepu](https://github.com/jpalepu)
