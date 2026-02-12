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
        print(f"Loading LLM: {model_name}...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            # Force float32 for Mac/MPS stability to avoid "probability tensor contains either inf, nan" errors
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32, 
                device_map="auto",
                trust_remote_code=True
            )
            
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
            print("LLM loaded.")
        except Exception as e:
            print(f"Error loading LLM: {e}")
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
Use markdown for better readability:
- Use **bold** for drug names and dosages.
- Use bullet points for lists.
- Use ### headers for sections.
- Keep the tone empathetic and professional.

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
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}), # Increased from 3 to 5 for better context
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
            # result contains the full prompt if using HuggingFacePipeline without careful stopping
            result = self.qa_chain.invoke({"query": question})
            response = result["result"]
            
            # Clean up: HuggingFacePipeline often includes the prompt in the output
            # We only want the part after <|im_start|>assistant
            target_str = "<|im_start|>assistant\n"
            if target_str in response:
                response = response.split(target_str)[-1].strip()
            
            # Also remove any trailing <|im_end|> if the model didn't stop properly
            response = response.replace("<|im_end|>", "").strip()
            
            # If the response is still empty or looks like the prompt, return a fallback
            if not response or "<|im_start|>" in response:
                return "I apologize, I'm having trouble formatting my response. Please try asking again."
                
            return response
        except Exception as e:
            return f"Error during query: {str(e)}"

# Singleton instance
_rag_service = None

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
