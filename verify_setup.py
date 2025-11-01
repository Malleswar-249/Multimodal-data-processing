"""
Setup verification script to check if all dependencies are installed correctly
"""
import sys

def check_dependency(module_name, import_name=None):
    """Check if a module can be imported"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    print("🔍 Checking dependencies...\n")
    
    dependencies = [
        ("streamlit", "streamlit"),
        ("google-generativeai", "google.generativeai"),
        ("chromadb", "chromadb"),
        ("PyPDF2", "PyPDF2"),
        ("docx", "docx"),
        ("pptx", "python_pptx"),
        ("Pillow", "PIL"),
        ("pytesseract", "pytesseract"),
        ("speechrecognition", "speech_recognition"),
        ("pydub", "pydub"),
        ("youtube-transcript-api", "youtube_transcript_api"),
        ("yt-dlp", "yt_dlp"),
        ("sentence-transformers", "sentence_transformers"),
        ("python-dotenv", "dotenv"),
    ]
    
    all_ok = True
    
    for package_name, import_name in dependencies:
        success, error = check_dependency(package_name, import_name)
        if success:
            print(f"✅ {package_name}")
        else:
            print(f"❌ {package_name} - {error}")
            all_ok = False
    
    print("\n" + "="*50)
    
    # Check environment variables
    print("\n🔑 Checking environment variables...\n")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("✅ GEMINI_API_KEY found")
    else:
        print("⚠️  GEMINI_API_KEY not found in .env file")
        print("   You can set it in the Streamlit app UI or add it to .env file")
    
    # Check Tesseract
    print("\n🔤 Checking Tesseract OCR...\n")
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
    except Exception as e:
        print(f"⚠️  Tesseract OCR not found: {e}")
        print("   Install Tesseract for image text extraction:")
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   macOS: brew install tesseract")
        print("   Linux: sudo apt-get install tesseract-ocr")
    
    print("\n" + "="*50)
    
    if all_ok:
        print("\n✅ All core dependencies are installed!")
        print("\nYou can now run:")
        print("  streamlit run app.py")
        print("or")
        print("  python cli.py --help")
    else:
        print("\n❌ Some dependencies are missing.")
        print("Please install them using:")
        print("  pip install -r requirements.txt")
    
    print()

if __name__ == "__main__":
    main()

