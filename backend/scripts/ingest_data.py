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
            documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {pdf_path.name}: {e}")

    print(f"Loaded {len(documents)} pages. Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Initializing embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print(f"Creating vector store in {persist_dir}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PERSIST_DIR = os.path.join(BASE_DIR, "backend", "instance", "vector_db")
    
    # Ensure instance directory exists
    os.makedirs(os.path.join(BASE_DIR, "backend", "instance"), exist_ok=True)
    
    ingest_pdfs(DATA_DIR, PERSIST_DIR)
