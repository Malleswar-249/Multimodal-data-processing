"""
Main Streamlit application for Multimodal Data Processing System
"""
import streamlit as st
import os
from dotenv import load_dotenv
from processors import FileProcessor
from database import VectorDatabase
from gemini_integration import GeminiAI

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Multimodal Data Processing System",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'db' not in st.session_state:
    try:
        st.session_state.db = VectorDatabase()
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        st.session_state.db = None

if 'processor' not in st.session_state:
    try:
        st.session_state.processor = FileProcessor()
    except Exception as e:
        st.error(f"Error initializing processor: {str(e)}")
        st.session_state.processor = None

if 'gemini' not in st.session_state:
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key and hasattr(st, 'secrets'):
            api_key = st.secrets.get('GEMINI_API_KEY', None)
        if api_key:
            st.session_state.gemini = GeminiAI(api_key=api_key)
        else:
            st.session_state.gemini = None
    except Exception as e:
        st.warning(f"Error initializing Gemini: {str(e)}")
        st.session_state.gemini = None

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []


def main():
    # Check if components are initialized
    if st.session_state.db is None:
        st.error("Database not initialized. Please refresh the page.")
        return
    if st.session_state.processor is None:
        st.error("File processor not initialized. Please refresh the page.")
        return
    
    st.title("📚 Multimodal Data Processing System")
    st.markdown("""
    This system can process multiple file types and answer questions using Gemini AI.
    
    **Supported formats:**
    - **Text:** PDF, DOCX, PPTX, MD, TXT
    - **Image:** PNG, JPG
    - **Audio/Video:** MP3, MP4, YouTube URLs
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            value=os.getenv('GEMINI_API_KEY', '') or (st.secrets.get('GEMINI_API_KEY', '') if hasattr(st, 'secrets') else ''),
            type="password",
            help="Enter your Gemini API key. Get one from https://makersuite.google.com/app/apikey"
        )
        
        if api_key:
            if st.session_state.gemini is None or st.session_state.gemini.api_key != api_key:
                try:
                    st.session_state.gemini = GeminiAI(api_key=api_key)
                    st.success("✅ API key configured!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        # Database stats
        st.subheader("📊 Database Status")
        if st.session_state.db:
            try:
                all_docs = st.session_state.db.get_all_documents()
                unique_files = len(set([doc['metadata'].get('file_name', 'unknown') for doc in all_docs])) if all_docs else 0
                st.info(f"Documents stored: {unique_files}")
            except Exception as e:
                st.error(f"Error reading database: {str(e)}")
        else:
            st.error("Database not available")
        
        if st.button("🗑️ Clear Database", type="secondary"):
            if st.session_state.db:
                try:
                    st.session_state.db.delete_all()
                    st.session_state.uploaded_files = []
                    st.success("Database cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing database: {str(e)}")
            else:
                st.error("Database not available")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Files", "🔍 Query", "📋 View Documents"])
    
    # Tab 1: Upload Files
    with tab1:
        st.header("Upload Files")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files to process",
            type=['pdf', 'docx', 'pptx', 'md', 'txt', 'png', 'jpg', 'jpeg', 'mp3', 'mp4'],
            accept_multiple_files=True
        )
        
        # YouTube URL input
        st.subheader("Or enter YouTube URL")
        youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        
        # Process button
        col1, col2 = st.columns([1, 4])
        with col1:
            process_btn = st.button("🚀 Process Files", type="primary")
        
        if process_btn:
            if uploaded_files or youtube_url:
                process_files(uploaded_files, youtube_url)
            else:
                st.warning("Please upload files or enter a YouTube URL")
    
    # Tab 2: Query
    with tab2:
        st.header("Ask Questions")
        
        if st.session_state.gemini is None:
            st.warning("⚠️ Please configure your Gemini API key in the sidebar to use the query feature.")
        else:
            query = st.text_area(
                "Enter your question",
                placeholder="Ask anything about the documents you've uploaded...",
                height=100
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                search_btn = st.button("🔍 Search & Answer", type="primary")
            
            if search_btn and query:
                answer_query(query)
            elif search_btn:
                st.warning("Please enter a question")
    
    # Tab 3: View Documents
    with tab3:
        st.header("Stored Documents")
        
        if not st.session_state.db:
            st.error("Database not available. Please refresh the page.")
            return
        
        try:
            all_docs = st.session_state.db.get_all_documents()
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
            all_docs = []
        
        if not all_docs:
            st.info("No documents stored yet. Upload files to get started.")
        else:
            # Group by file name
            files_dict = {}
            for doc in all_docs:
                file_name = doc['metadata'].get('file_name', 'unknown')
                if file_name not in files_dict:
                    files_dict[file_name] = []
                files_dict[file_name].append(doc)
            
            for file_name, chunks in files_dict.items():
                with st.expander(f"📄 {file_name} ({len(chunks)} chunks)"):
                    st.write(f"**Type:** {chunks[0]['metadata'].get('file_type', 'unknown')}")
                    
                    # Show combined text
                    combined_text = "\n\n".join([chunk['text'] for chunk in chunks])
                    if len(combined_text) > 1000:
                        st.text_area("Content", combined_text[:1000] + "...", height=200, disabled=True)
                    else:
                        st.text_area("Content", combined_text, height=200, disabled=True)


def process_files(uploaded_files, youtube_url=None):
    """Process uploaded files and YouTube URLs"""
    if not st.session_state.processor:
        st.error("File processor not available. Please refresh the page.")
        return
    if not st.session_state.db:
        st.error("Database not available. Please refresh the page.")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_items = len(uploaded_files) if uploaded_files else 0
    if youtube_url:
        total_items += 1
    
    processed_count = 0
    
    try:
        # Process uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Process file
                result = st.session_state.processor.process_file(
                    file_data=uploaded_file,
                    file_name=uploaded_file.name
                )
                
                if result['text']:
                    # Add to database
                    doc_id = st.session_state.db.add_document(
                        text=result['text'],
                        metadata=result['metadata'],
                        image_data=result.get('image_data', '')
                    )
                    
                    if doc_id:
                        st.session_state.uploaded_files.append({
                            'name': uploaded_file.name,
                            'id': doc_id,
                            'type': result['metadata']['file_type']
                        })
                        st.success(f"✅ Processed: {uploaded_file.name}")
                    else:
                        st.warning(f"⚠️ Could not add {uploaded_file.name} to database (empty content)")
                else:
                    st.error(f"❌ Failed to extract content from {uploaded_file.name}")
                
                processed_count += 1
                progress_bar.progress(processed_count / total_items if total_items > 0 else 1)
        
        # Process YouTube URL
        if youtube_url:
            status_text.text(f"Processing YouTube URL...")
            result = st.session_state.processor.process_youtube_url(youtube_url)
            
            if result['text']:
                doc_id = st.session_state.db.add_document(
                    text=result['text'],
                    metadata=result['metadata'],
                    image_data=result.get('image_data', '')
                )
                
                if doc_id:
                    st.success(f"✅ Processed YouTube URL")
                else:
                    st.warning(f"⚠️ Could not add YouTube URL to database")
            else:
                st.error(f"❌ Failed to process YouTube URL")
            
            processed_count += 1
            progress_bar.progress(processed_count / total_items if total_items > 0 else 1)
        
        status_text.text("✅ Processing complete!")
        progress_bar.progress(1.0)
        
    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        status_text.text("❌ Processing failed!")


def answer_query(query):
    """Answer user query using retrieved context and Gemini AI"""
    if not st.session_state.db:
        st.error("Database not available. Please refresh the page.")
        return
    if not st.session_state.gemini:
        st.error("Gemini AI not configured. Please add your API key in the sidebar.")
        return
    
    with st.spinner("Searching documents and generating answer..."):
        # Search database
        try:
            search_results = st.session_state.db.search(query, n_results=5)
        except Exception as e:
            st.error(f"Error searching database: {str(e)}")
            return
        
        if not search_results:
            st.warning("No relevant documents found. Please upload some files first.")
            return
        
        # Show relevant context
        with st.expander("📚 Relevant Context Retrieved"):
            for i, result in enumerate(search_results[:3], 1):
                st.write(f"**Source {i}:** {result['metadata'].get('file_name', 'unknown')}")
                st.write(result['text'][:300] + "..." if len(result['text']) > 300 else result['text'])
                st.divider()
        
        # Generate answer using Gemini
        try:
            answer = st.session_state.gemini.generate_response(query, context=search_results)
            
            st.subheader("💡 Answer")
            st.write(answer)
            
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")


if __name__ == "__main__":
    main()

