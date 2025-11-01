"""
Gemini AI integration for generating responses
"""
import google.generativeai as genai
import os
from typing import List, Dict
import base64


class GeminiAI:
    """Handle Gemini AI interactions"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini AI client"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it during initialization.")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - try newer model names first
        self.model = None
        self.multimodal_model = None
        
        # Try different model names (newer models first, using full model path)
        model_names = [
            'models/gemini-2.5-flash',  # Fast and efficient
            'models/gemini-2.5-pro',    # More capable
            'models/gemini-flash-latest', # Latest flash
            'models/gemini-pro-latest',  # Latest pro
            'models/gemini-2.0-flash',   # Stable 2.0 version
        ]
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test if it works with a simple query
                test_response = self.model.generate_content("Hi")
                if test_response and test_response.text:
                    print(f"Successfully initialized model: {model_name}")
                    # Use the same model for multimodal (newer models support both)
                    self.multimodal_model = self.model
                    break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {str(e)}")
                continue
        
        # If still no model, try to list available models
        if self.model is None:
            try:
                print("Attempting to list available models...")
                models = genai.list_models()
                available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
                print(f"Available models: {available_models}")
                
                # Try the first available model
                if available_models:
                    model_to_use = available_models[0].split('/')[-1]  # Get just the model name
                    self.model = genai.GenerativeModel(model_to_use)
                    self.multimodal_model = self.model
                    print(f"Using model: {model_to_use}")
            except Exception as e:
                print(f"Error listing models: {str(e)}")
                raise ValueError(f"Could not initialize any Gemini model. Error: {str(e)}")
    
    def generate_response(self, query: str, context: List[Dict] = None, image_data: str = None) -> str:
        """
        Generate response using Gemini AI
        
        Args:
            query: User's natural language query
            context: List of relevant document chunks from database
            image_data: Base64 encoded image data (if query involves an image)
        
        Returns:
            Generated response string
        """
        if not self.model:
            return "Gemini AI model is not initialized. Please check your API key."
        
        try:
            # Build context from retrieved documents
            context_text = ""
            if context:
                context_text = "\n\n".join([
                    f"Document {i+1} (from {doc.get('metadata', {}).get('file_name', 'unknown')}):\n{doc.get('text', '')}"
                    for i, doc in enumerate(context[:5])  # Limit to top 5 results
                ])
            
            # Construct prompt
            if context_text:
                prompt = f"""Based on the following information from processed documents, please answer the user's question.

Context from documents:
{context_text}

User's question: {query}

Please provide a clear, comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, please say so."""
            else:
                prompt = f"""Answer the following question:

{query}

Please provide a clear and helpful response."""
            
            # Generate response
            if image_data and self.multimodal_model:
                # For multimodal queries with images
                try:
                    import PIL.Image as PILImage
                    import io
                    img_bytes = base64.b64decode(image_data)
                    img = PILImage.open(io.BytesIO(img_bytes))
                    
                    response = self.multimodal_model.generate_content([prompt, img])
                    if response and response.text:
                        return response.text
                    else:
                        return "Response generated but was empty. Please try again."
                except Exception as e:
                    # Fallback to text-only
                    try:
                        response = self.model.generate_content(prompt)
                        if response and response.text:
                            return response.text
                        else:
                            return f"Response was empty. Error: {str(e)}"
                    except Exception as e2:
                        return f"Error generating response: {str(e2)}"
            else:
                # Text-only response
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text
                else:
                    return "Response generated but was empty. Please try again."
                
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"Model not found error: {error_msg}\n\nThe Gemini model may have changed. Please check the available models."
            return f"Error generating response: {error_msg}\n\nPlease check your Gemini API key and ensure it's valid."
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate summary of text"""
        if not self.model:
            return "Gemini AI model is not initialized."
        
        try:
            prompt = f"Please provide a brief summary (maximum {max_length} words) of the following text:\n\n{text}"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"

