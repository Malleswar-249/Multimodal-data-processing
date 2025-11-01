"""
Command-line interface for Multimodal Data Processing System
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from processors import FileProcessor
from database import VectorDatabase
from gemini_integration import GeminiAI

# Load environment variables
load_dotenv()


def process_file_command(file_path: str, db: VectorDatabase, processor: FileProcessor):
    """Process a single file"""
    print(f"Processing {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    result = processor.process_file(file_path=file_path)
    
    if result['text']:
        doc_id = db.add_document(
            text=result['text'],
            metadata=result['metadata'],
            image_data=result.get('image_data', '')
        )
        if doc_id:
            print(f"✅ Successfully processed and stored: {file_path}")
            return True
        else:
            print(f"⚠️ Could not store {file_path} (empty content)")
            return False
    else:
        print(f"❌ Failed to extract content from {file_path}")
        return False


def process_youtube_command(url: str, db: VectorDatabase, processor: FileProcessor):
    """Process a YouTube URL"""
    print(f"Processing YouTube URL: {url}...")
    
    result = processor.process_youtube_url(url)
    
    if result['text']:
        doc_id = db.add_document(
            text=result['text'],
            metadata=result['metadata'],
            image_data=result.get('image_data', '')
        )
        if doc_id:
            print(f"✅ Successfully processed YouTube URL")
            return True
        else:
            print(f"⚠️ Could not store YouTube URL")
            return False
    else:
        print(f"❌ Failed to process YouTube URL")
        return False


def query_command(query: str, db: VectorDatabase, gemini: GeminiAI):
    """Query the database"""
    print(f"\nSearching for: {query}\n")
    
    # Search database
    search_results = db.search(query, n_results=5)
    
    if not search_results:
        print("No relevant documents found.")
        return
    
    print("📚 Relevant Context:")
    print("-" * 50)
    for i, result in enumerate(search_results[:3], 1):
        print(f"\nSource {i}: {result['metadata'].get('file_name', 'unknown')}")
        print(result['text'][:200] + "..." if len(result['text']) > 200 else result['text'])
        print()
    
    # Generate answer
    print("\n💡 Answer:")
    print("-" * 50)
    try:
        answer = gemini.generate_response(query, context=search_results)
        print(answer)
    except Exception as e:
        print(f"Error: {str(e)}")


def list_documents_command(db: VectorDatabase):
    """List all stored documents"""
    all_docs = db.get_all_documents()
    
    if not all_docs:
        print("No documents stored.")
        return
    
    # Group by file name
    files_dict = {}
    for doc in all_docs:
        file_name = doc['metadata'].get('file_name', 'unknown')
        if file_name not in files_dict:
            files_dict[file_name] = []
        files_dict[file_name].append(doc)
    
    print(f"\n📋 Stored Documents ({len(files_dict)} files):\n")
    for file_name, chunks in files_dict.items():
        print(f"  📄 {file_name} ({len(chunks)} chunks)")
        print(f"     Type: {chunks[0]['metadata'].get('file_type', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(
        description="Multimodal Data Processing System - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a file
  python cli.py process document.pdf
  
  # Process multiple files
  python cli.py process doc1.pdf doc2.docx image.png
  
  # Process YouTube URL
  python cli.py youtube "https://www.youtube.com/watch?v=..."
  
  # Query the database
  python cli.py query "What is the main topic?"
  
  # List all documents
  python cli.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process file(s)')
    process_parser.add_argument('files', nargs='+', help='File path(s) to process')
    
    # YouTube command
    youtube_parser = subparsers.add_parser('youtube', help='Process YouTube URL')
    youtube_parser.add_argument('url', help='YouTube video URL')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the database')
    query_parser.add_argument('question', help='Question to ask')
    
    # List command
    subparsers.add_parser('list', help='List all stored documents')
    
    # Clear command
    subparsers.add_parser('clear', help='Clear all documents from database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize components
    db = VectorDatabase()
    processor = FileProcessor()
    
    # Get Gemini API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Query feature will not work.")
        print("Set it in .env file or environment variable.")
        gemini = None
    else:
        try:
            gemini = GeminiAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            gemini = None
    
    # Execute command
    if args.command == 'process':
        for file_path in args.files:
            process_file_command(file_path, db, processor)
    
    elif args.command == 'youtube':
        process_youtube_command(args.url, db, processor)
    
    elif args.command == 'query':
        if not gemini:
            print("Error: Gemini API key required for queries.")
            sys.exit(1)
        query_command(args.question, db, gemini)
    
    elif args.command == 'list':
        list_documents_command(db)
    
    elif args.command == 'clear':
        confirm = input("Are you sure you want to clear all documents? (yes/no): ")
        if confirm.lower() == 'yes':
            db.delete_all()
            print("✅ Database cleared!")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()

