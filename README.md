# Multimodal Data Processing System

A comprehensive system that processes multiple file types (text, images, audio/video) and answers natural language queries using Google's Gemini AI.

## Features

- **Multiple File Format Support:**
  - Text: PDF, DOCX, PPTX, MD, TXT
  - Images: PNG, JPG (with OCR)
  - Audio/Video: MP3, MP4, YouTube URLs

- **Intelligent Search:** Vector-based semantic search using ChromaDB
- **AI-Powered Responses:** Uses Google Gemini Pro for generating answers
- **User-Friendly Interface:** Streamlit web interface

## Prerequisites

- Python 3.8 or higher
- Gemini API Key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Tesseract OCR (for image text extraction)
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. (Optional) Configure Tesseract OCR path:
   - Windows: Add Tesseract to PATH or set in code
   - The code will try to use default installation paths

5. Verify installation (optional):
```bash
python verify_setup.py
```

## Usage

### Option 1: Streamlit Web Interface (Recommended)

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. The application will open in your browser (usually at `http://localhost:8501`)

3. **Upload Files:**
   - Go to the "Upload Files" tab
   - Upload one or more files
   - Or enter a YouTube URL
   - Click "Process Files"

4. **Ask Questions:**
   - Go to the "Query" tab
   - Enter your question in natural language
   - Click "Search & Answer"
   - The system will search through your documents and generate an answer using Gemini AI

5. **View Documents:**
   - Go to the "View Documents" tab
   - See all processed documents and their content

### Option 2: Command Line Interface

```bash
# Process a file
python cli.py process document.pdf

# Process multiple files
python cli.py process doc1.pdf doc2.docx image.png

# Process YouTube URL
python cli.py youtube "https://www.youtube.com/watch?v=..."

# Query the database
python cli.py query "What is the main topic?"

# List all stored documents
python cli.py list

# Clear database
python cli.py clear
```

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── processors.py          # File processing logic for all file types
├── database.py            # Vector database operations (ChromaDB)
├── gemini_integration.py  # Gemini AI integration
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
└── README.md             # This file
```

## How It Works

1. **File Processing:**
   - Different processors extract text/content from various file types
   - Images are processed with OCR (Tesseract)
   - Audio/video files are transcribed using speech recognition
   - YouTube videos extract transcripts

2. **Storage:**
   - Processed content is split into chunks
   - Chunks are embedded using sentence transformers
   - Embeddings are stored in ChromaDB vector database

3. **Query Processing:**
   - User query is embedded
   - Similar document chunks are retrieved from the database
   - Relevant context is sent to Gemini AI
   - Gemini generates a natural language response

## Troubleshooting

- **Tesseract OCR not found:** Install Tesseract and ensure it's in your PATH
- **Gemini API errors:** Check your API key is valid and has not exceeded rate limits
- **Audio transcription issues:** Requires Google Speech Recognition API (free tier available)
- **Memory issues with large files:** Consider processing files individually

## Notes

- The free tier of Gemini API has rate limits
- Large audio/video files may take time to process
- YouTube transcripts may not be available for all videos
- Image OCR quality depends on image clarity and text visibility

## License

This project is for educational purposes.

