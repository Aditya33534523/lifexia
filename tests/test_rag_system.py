import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.services.rag_service import get_rag_service

def test_query():
    print("Testing RAG System...")
    service = get_rag_service()
    
    questions = [
        "What is the standard dosage for Paracetamol according to NLEM 2022?",
        "Tell me about the Indian Pharmacopoeia (2022)."
    ]
    
    for q in questions:
        print(f"\nQuestion: {q}")
        response = service.query(q)
        print(f"Response: {response}")

if __name__ == "__main__":
    test_query()
