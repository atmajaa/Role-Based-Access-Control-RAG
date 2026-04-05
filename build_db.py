import pypdf
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

departments = ["engineering", "hr", "sales"]

for dept in departments:
    print(f"Building DB for: {dept}...")

    pdf_dir = f"./dept_pdfs/{dept}"
    db_dir  = f"./dept_dbs/{dept}"

    # Find the PDF in that dept folder
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"  No PDF found in {pdf_dir}, skipping...")
        continue

    pdf_path = f"{pdf_dir}/{pdf_files[0]}"

    # Read the PDF
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        full_text = "".join(page.extract_text() for page in reader.pages)

    # Chunk it
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(full_text)
    print(f"  Created {len(chunks)} chunks")

    # Build and save vector DB
    Chroma.from_texts(
        texts=chunks,
        embedding=embedding_model,
        persist_directory=db_dir
    )
    print(f"  Done! Saved to {db_dir}")

print("\nAll departments done!")