import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import ML dependencies - gracefully handle if not available
try:
    from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
    from langchain_community.vectorstores import Chroma
    from langchain_core.prompts import PromptTemplate
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML dependencies not available: {e}. RAG service will run in fallback mode.")
    ML_AVAILABLE = False

class RAGService:
    def __init__(self):
        if not ML_AVAILABLE:
            logger.warning("RAG Service running in fallback mode (no ML dependencies)")
            self.vector_store = None
            self.llm = None
            self.template = None
            self.embeddings = None
            return

        BASE_DIR = Path(__file__).resolve().parent
        PERSIST_DIR = os.path.join(BASE_DIR, "instance", "vector_db")
        
        print("Initializing RAG Service...")
        
        # 1. Load Embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 2. Load Vector Store
        try:
            if not os.path.exists(PERSIST_DIR):
                print(f"Warning: Vector DB not found at {PERSIST_DIR}. Please run ingestion script first.")
                self.vector_store = None
            else:
                self.vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=self.embeddings)
                print("Vector Store loaded.")
        except Exception as e:
            print(f"Error loading Vector Store (likely Python 3.14/Pydantic v1 incompatibility): {e}")
            print("Falling back to non-RAG mode.")
            self.vector_store = None

        # 3. Load LLM
        model_name = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
        use_gpu = os.getenv("USE_GPU", "False").lower() == "true"
        
        print(f"Loading LLM: {model_name}...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # For systems with adequate RAM (12GB+) or GPU
            # Qwen2.5-3B provides excellent medical Q&A quality
            if use_gpu and torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.float16
            else:
                device = "cpu"
                torch_dtype = torch.float32
            
            print(f"Using device: {device}")
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if device != "cpu":
                model = model.to(device)
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=256,
                temperature=0.0, # Greedy decoding for speed
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            self.llm = HuggingFacePipeline(pipeline=pipe)
            print("LLM loaded successfully.")
        except Exception as e:
            print(f"Error loading LLM: {e}")
            print("Chat service will not be available.")
            self.llm = None

        # 4. Create QA Chain
        if self.llm:
            # Qwen 2.5 uses ChatML format with <|im_start|> and <|im_end|>
            template = """<|im_start|>system
You are LifeXia, an intelligent pharmacy assistant. Provide a helpful, professional, and accurate answer.
{context_msg}

Guidelines:
- **Accuracy**: Prioritize accuracy. Do not hallucinate or guess drug interactions or dosages.
- **Safety**: If a query involves critical safety or severe symptoms, advise consulting a healthcare professional immediately.
- **Clarity**: Provide clear, concise information suitable for the user's level of understanding.

Question:
{question}<|im_end|>
<|im_start|>assistant
"""
            self.template = template
            print("Qwen model template initialized.")
        else:
            self.template = None

    def query(self, question: str, user_type: str = 'patient', context: str = ''):
        if not self.llm:
            return "Chat service is still initializing or missing resources. Please try again later."
        
        try:
            # RAG Fallback logic
            context = ""
            context_msg = ""
            
            if self.vector_store:
                try:
                    docs = self.vector_store.similarity_search(question, k=3)
                    context = "\n".join([d.page_content for d in docs])
                    context_msg = f"Use the following context to help answer:\n{context}"
                except Exception as e:
                    print(f"Similarity search failed: {e}")
            
            prompt = self.template.format(
                context_msg=context_msg,
                question=question
            )
            
            # Manual invocation as RetrievalQA might fail due to Pydantic
            response = self.llm.invoke(prompt)
            
            # Clean up response
            target_str = "<|im_start|>assistant\n"
            if target_str in response:
                response = response.split(target_str)[-1].strip()
            
            response = response.replace("<|im_end|>", "").strip()
            
            if not response or "<|im_start|>" in response:
                return "I apologize, I'm having trouble formatting my response. Please try asking again."
                
            return response
        except Exception as e:
            print(f"Error during query: {str(e)}")
            return f"I encountered an error processing your question. Please try rephrasing it."

# Singleton instance
_rag_service = None

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service