"""
Vector database for storing and retrieving document embeddings
"""
import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import os


class VectorDatabase:
    """Manages vector database operations using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and embedding model"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        except Exception as e:
            raise Exception(f"Failed to initialize ChromaDB client: {str(e)}")
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="multimodal_documents",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise Exception(f"Failed to create/get collection: {str(e)}")
        
        # Initialize embedding model (can be slow, so we'll try but don't fail if it doesn't work)
        self.embedding_model = None
        try:
            import warnings
            warnings.filterwarnings("ignore")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}. Some features may be limited.")
            self.embedding_model = None
    
    def add_document(self, text: str, metadata: Dict, image_data: str = "") -> str:
        """
        Add document to vector database
        Returns document ID
        """
        if not text or text.strip() == "":
            return None
        
        # Split text into chunks (for better retrieval)
        chunks = self._chunk_text(text, chunk_size=500, overlap=100)
        
        doc_id = str(uuid.uuid4())
        document_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            document_ids.append(chunk_id)
            
            # Create enhanced metadata
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "has_image": bool(image_data),
                "doc_id": doc_id
            }
            
            # Store image data in first chunk metadata if present
            if image_data and i == 0:
                chunk_metadata["image_data"] = image_data
            
            # Generate embedding
            if self.embedding_model:
                embedding = self.embedding_model.encode(chunk).tolist()
            else:
                # Fallback: use simple hash-based embedding (not ideal but works)
                embedding = [hash(chunk) % 1000 / 1000.0] * 384
            
            # Add to collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[chunk_metadata]
            )
        
        return doc_id
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar documents
        Returns list of dictionaries with 'text', 'metadata', and 'distance'
        """
        if not query or query.strip() == "":
            return []
        
        # Generate query embedding
        if self.embedding_model:
            query_embedding = self.embedding_model.encode(query).tolist()
        else:
            query_embedding = [hash(query) % 1000 / 1000.0] * 384
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents from database"""
        results = self.collection.get()
        
        documents = []
        if results['ids']:
            for i in range(len(results['ids'])):
                documents.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
        
        return documents
    
    def delete_all(self):
        """Delete all documents from database"""
        try:
            self.client.delete_collection(name="multimodal_documents")
            self.collection = self.client.get_or_create_collection(
                name="multimodal_documents",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error deleting collection: {e}")
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # If found a good break point
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks

