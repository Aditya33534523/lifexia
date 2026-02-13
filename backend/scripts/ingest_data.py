#!/usr/bin/env python3
"""
Improved Data Ingestion Script for LifeXia
- Multiple PDF parsing methods with fallbacks
- Better error handling
- Progress tracking
- Corrupted file recovery
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


class RobustPDFLoader:
    """Loads PDFs using multiple methods with fallbacks"""
    
    @staticmethod
    def load_with_pypdf(pdf_path: str) -> Tuple[List[Document], str]:
        """Method 1: PyPDFLoader (original method)"""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            return docs, "PyPDFLoader"
        except Exception as e:
            raise Exception(f"PyPDFLoader failed: {e}")
    
    @staticmethod
    def load_with_pdfplumber(pdf_path: str) -> Tuple[List[Document], str]:
        """Method 2: pdfplumber (more robust for corrupted PDFs)"""
        try:
            import pdfplumber
            
            documents = []
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            doc = Document(
                                page_content=text,
                                metadata={
                                    'source': Path(pdf_path).name,
                                    'page': i
                                }
                            )
                            documents.append(doc)
                    except Exception as e:
                        print(f"    ⚠️ Warning: Page {i} failed: {str(e)[:50]}")
                        continue
            
            return documents, "pdfplumber"
        except Exception as e:
            raise Exception(f"pdfplumber failed: {e}")
    
    @staticmethod
    def load_with_pymupdf(pdf_path: str) -> Tuple[List[Document], str]:
        """Method 3: PyMuPDF/fitz (most robust)"""
        try:
            import fitz  # PyMuPDF
            
            documents = []
            pdf = fitz.open(pdf_path)
            
            for i in range(pdf.page_count):
                try:
                    page = pdf[i]
                    text = page.get_text()
                    
                    if text and text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={
                                'source': Path(pdf_path).name,
                                'page': i + 1
                            }
                        )
                        documents.append(doc)
                except Exception as e:
                    print(f"    ⚠️ Warning: Page {i + 1} failed: {str(e)[:50]}")
                    continue
            
            pdf.close()
            return documents, "PyMuPDF"
        except Exception as e:
            raise Exception(f"PyMuPDF failed: {e}")
    
    @classmethod
    def load(cls, pdf_path: str) -> Tuple[List[Document], str]:
        """Try all methods in order until one succeeds"""
        methods = [
            cls.load_with_pypdf,
            cls.load_with_pdfplumber,
            cls.load_with_pymupdf
        ]
        
        last_error = None
        for method in methods:
            try:
                docs, method_name = method(pdf_path)
                if docs:
                    return docs, method_name
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"All PDF loading methods failed. Last error: {last_error}")


def ingest_pdfs_improved(data_dir: str, persist_dir: str):
    """Improved PDF ingestion with multiple fallback methods"""
    
    print(f"Scanning for PDFs in {data_dir}...")
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found.")
        return
    
    print(f"Found {len(pdf_files)} PDF files\n")
    
    all_documents = []
    successful_files = []
    failed_files = []
    
    for pdf_path in pdf_files:
        print(f"Loading {pdf_path.name}...")
        
        try:
            docs, method = RobustPDFLoader.load(str(pdf_path))
            all_documents.extend(docs)
            successful_files.append(pdf_path.name)
            print(f"  ✓ Loaded {len(docs)} pages from {pdf_path.name} (using {method})")
        except Exception as e:
            failed_files.append((pdf_path.name, str(e)))
            print(f"  ✗ Error loading {pdf_path.name}: {e}")
            continue
    
    if not all_documents:
        print("\n❌ No documents were successfully loaded. Exiting.")
        return
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✓ Successfully loaded: {len(successful_files)} files")
    print(f"  ✗ Failed: {len(failed_files)} files")
    print(f"  📄 Total pages: {len(all_documents)}")
    print(f"{'='*60}\n")
    
    if failed_files:
        print("Failed files:")
        for filename, error in failed_files:
            print(f"  • {filename}: {error[:80]}")
        print()
    
    # Split into chunks
    print("Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(all_documents)
    print(f"Created {len(chunks)} chunks.\n")
    
    if not chunks:
        print("No chunks created. Exiting.")
        return
    
    # Initialize embeddings
    print("Initializing embeddings (this may take a while)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Create or update vector store
    print(f"Creating/updating vector store in {persist_dir}...")
    os.makedirs(persist_dir, exist_ok=True)
    
    # Check if vector store exists
    if os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
        print("Existing vector store found. Adding new documents...")
        vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        
        # Add in batches
        batch_size = 500
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
            vector_store.add_documents(batch)
    else:
        print("Creating new vector store...")
        # Process in batches
        batch_size = 500
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
            
            if i == 0:
                vector_store = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=persist_dir
                )
            else:
                vector_store.add_documents(batch)
    
    print(f"\n{'='*60}")
    print("✓ Ingestion complete!")
    print(f"Vector database saved to: {persist_dir}")
    print(f"{'='*60}")


def install_optional_dependencies():
    """Install optional PDF parsing libraries"""
    print("Installing optional PDF parsing libraries...")
    print("This will improve handling of corrupted PDFs.\n")
    
    packages = [
        "pdfplumber",
        "PyMuPDF"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        os.system(f"pip install {package} --break-system-packages -q")
    
    print("\n✓ Optional dependencies installed!")
    print("Run the ingestion script again to use the improved loaders.\n")


if __name__ == "__main__":
    # Get project root - where backend/ folder is located
    script_path = Path(__file__).resolve()
    
    # If script is in backend/scripts/, go up 2 levels to project root
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "backend":
        BASE_DIR = script_path.parent.parent.parent
    # If running from project root  
    elif (Path.cwd() / "backend").exists():
        BASE_DIR = Path.cwd()
    else:
        BASE_DIR = script_path.parent.parent
    
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PERSIST_DIR = os.path.join(BASE_DIR, "backend", "instance", "vector_db")
    
    print(f"📂 Project root: {BASE_DIR}")
    print(f"📁 Looking for PDFs in: {DATA_DIR}")
    print(f"💾 Vector DB path: {PERSIST_DIR}")
    print()
    
    # Ensure instance directory exists
    os.makedirs(os.path.join(BASE_DIR, "backend", "instance"), exist_ok=True)
    
    # Check for optional dependencies
    if len(sys.argv) > 1 and sys.argv[1] == "--install-deps":
        install_optional_dependencies()
    else:
        try:
            import pdfplumber
            import fitz
            print("✓ Optional dependencies available\n")
        except ImportError:
            print("⚠️  Optional PDF parsing libraries not found.")
            print("For better handling of corrupted PDFs, run:")
            print("  python backend/scripts/ingest_data_improved.py --install-deps\n")
        
        ingest_pdfs_improved(DATA_DIR, PERSIST_DIR)