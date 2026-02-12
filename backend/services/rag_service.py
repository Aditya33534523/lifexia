import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

class RAGService:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        PERSIST_DIR = os.path.join(BASE_DIR, "backend", "instance", "vector_db")
        
        print("Initializing RAG Service...")
        
        # 1. Load Embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 2. Load Vector Store
        if not os.path.exists(PERSIST_DIR):
            print(f"Warning: Vector DB not found at {PERSIST_DIR}. Please run ingestion script first.")
            self.vector_store = None
        else:
            self.vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=self.embeddings)
            print("Vector Store loaded.")

        # 3. Load LLM
        model_name = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
        use_gpu = os.getenv("USE_GPU", "False").lower() == "true"
        
        print(f"Loading LLM: {model_name}...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Determine device
            if use_gpu and torch.backends.mps.is_available():
                device = "mps"
                torch_dtype = torch.float16
            elif use_gpu and torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.float16
            else:
                device = "cpu"
                torch_dtype = torch.float32
            
            print(f"Using device: {device}")
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                device_map=device if device != "cpu" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if device == "cpu":
                model = model.to(device)
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            self.llm = HuggingFacePipeline(pipeline=pipe)
            print("LLM loaded successfully.")
        except Exception as e:
            print(f"Error loading LLM: {e}")
            print("RAG service will not be available.")
            self.llm = None

        # 4. Create QA Chain
        if self.vector_store and self.llm:
            template = """<|im_start|>system
You are LifeXia, an intelligent pharmacy assistant. Use the following pharmaceutical context to provide a helpful, professional, and accurate answer.
Your responses must be based ONLY on the provided context. If the context does not contain the answer, politely state that you can only provide information based on official availability.

Important Guidelines:
- **Accuracy**: Prioritize accuracy. Do not hallucinate or guess drug interactions or dosages.
- **Safety**: If a query involves critical safety or severe symptoms, advise consulting a healthcare professional immediately.
- **Structure**: Use markdown (bold for names/dosages, bullet points for lists) for readability.
- **Tone**: Empathetic, professional, and concise.

If the context doesn't contain the answer, politely state that you can only provide information based on the official documents available to you.

Context:
{context}<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant
"""
            QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
            )
            print("QA Chain initialized.")
        else:
            self.qa_chain = None

    def query(self, question: str):
        if not self.qa_chain:
            return "RAG service is still initializing or missing resources. Please try again later."
        
        try:
            result = self.qa_chain.invoke({"query": question})
            response = result["result"]
            
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