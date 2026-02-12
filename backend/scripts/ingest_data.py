import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def ingest_pdfs(data_dir: str, persist_dir: str):
    print(f"Scanning for PDFs in {data_dir}...")
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return

    documents = []
    for pdf_path in pdf_files:
        print(f"Loading {pdf_path.name}...")
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            documents.extend(docs)
            print(f"  ✓ Loaded {len(docs)} pages from {pdf_path.name}")
        except Exception as e:
            print(f"  ✗ Error loading {pdf_path.name}: {e}")

    if not documents:
        print("No documents were successfully loaded. Exiting.")
        return

    print(f"\nTotal loaded: {len(documents)} pages. Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    if not chunks:
        print("No chunks created. Exiting.")
        return

    print("\nInitializing embeddings (this may take a while)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print(f"Creating vector store in {persist_dir}...")
    os.makedirs(persist_dir, exist_ok=True)
    
    # Process in batches to avoid memory issues
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
        
        if i == 0:
            # Create new vector store with first batch
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_dir
            )
        else:
            # Add to existing vector store
            vector_store.add_documents(batch)
    
    print("\n✓ Ingestion complete!")
    print(f"Vector database saved to: {persist_dir}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PERSIST_DIR = os.path.join(BASE_DIR, "backend", "instance", "vector_db")
    
    # Ensure instance directory exists
    os.makedirs(os.path.join(BASE_DIR, "backend", "instance"), exist_ok=True)
    
    ingest_pdfs(DATA_DIR, PERSIST_DIR)