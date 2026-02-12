#!/usr/bin/env python3
"""
LifeXia - Data Directory Setup and Verification
Fixes the data directory path issue
"""

import os
from pathlib import Path

def setup_data_directory():
    """Setup the correct data directory structure"""
    
    print("=" * 60)
    print("LifeXia - Data Directory Setup")
    print("=" * 60)
    print()
    
    # Determine project root (where this script is run from)
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Find project root (look for backend folder)
    if (current_dir / "backend").exists():
        project_root = current_dir
    elif (current_dir.parent / "backend").exists():
        project_root = current_dir.parent
    else:
        project_root = current_dir
    
    print(f"Project root: {project_root}")
    print()
    
    # Create data directory at project root
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"✓ Data directory: {data_dir}")
    print()
    
    # Check for PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if pdf_files:
        print(f"✓ Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  - {pdf.name} ({size_mb:.2f} MB)")
    else:
        print("⚠️  No PDF files found in data directory!")
        print()
        print("To add your PDF files:")
        print(f"  1. Place your PDF files in: {data_dir}")
        print(f"  2. Or copy from your previous location:")
        print(f"     cp /path/to/your/pdfs/*.pdf {data_dir}/")
        print()
        
        # Check if there's a previous ingestion log
        print("Checking for previously ingested data...")
        vector_db = project_root / "backend" / "instance" / "vector_db"
        
        if vector_db.exists():
            print(f"✓ Found existing vector database at: {vector_db}")
            print("  Your data is already ingested. No need to re-ingest.")
        else:
            print("✗ No existing vector database found.")
            print("  You'll need to add PDFs and run ingestion.")
    
    print()
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    
    if not pdf_files:
        print(f"1. Add PDF files to: {data_dir}")
        print("2. Run: python3 backend/scripts/ingest_data_improved.py")
    else:
        print(f"PDFs are ready! Run ingestion:")
        print("  python3 backend/scripts/ingest_data_improved.py")
    
    print()
    
    # Update the ingestion script path
    update_ingestion_script_path(project_root, data_dir)
    
    return data_dir


def update_ingestion_script_path(project_root, data_dir):
    """Create a corrected version of the ingestion script"""
    
    original_script = project_root / "backend" / "scripts" / "ingest_data.py"
    
    if not original_script.exists():
        print("⚠️  Original ingestion script not found.")
        return
    
    # Read the original script
    with open(original_script, 'r') as f:
        content = f.read()
    
    # Fix the DATA_DIR path - it should be at project root, not backend/data
    if 'BASE_DIR, "data"' in content:
        print("✓ Script already uses correct path (project_root/data)")
    elif 'backend", "data"' in content:
        print("Fixing DATA_DIR path in ingestion script...")
        # The script incorrectly looks in backend/data instead of project_root/data
        content = content.replace(
            'BASE_DIR = Path(__file__).resolve().parent.parent.parent',
            f'# Fixed: Use absolute path to data directory\nBASE_DIR = Path("{project_root}")'
        )
        
        # Write corrected version
        corrected_script = project_root / "backend" / "scripts" / "ingest_data_fixed.py"
        with open(corrected_script, 'w') as f:
            f.write(content)
        
        print(f"✓ Created corrected script: {corrected_script}")
        print("  Use this instead: python3 backend/scripts/ingest_data_fixed.py")


if __name__ == "__main__":
    setup_data_directory()