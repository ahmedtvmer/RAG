"""
To Ingest data:
- Add document files in "raw_documents" folder
- Run: uv run python scripts/ingest_data.py
"""

import os
import requests
from bs4 import BeautifulSoup
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# URLs to ingest
urls = [
    "https://en.wikipedia.org/wiki/Generative_pre-trained_transformer",
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://en.wikipedia.org/wiki/Transformer_(machine_learning_model)",
    "https://en.wikipedia.org/wiki/Attention_(machine_learning)",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
]

directory_path = "./raw_documents" # add document files here


def get_vector_db():
    """Initializes the model and DB connection exactly once."""
    embeddings = HuggingFaceEmbeddings(model_name='./local_models/embedder')
    return Chroma(
        persist_directory='./db',
        embedding_function=embeddings
    )


def ingest_url(url, vectorDB):
    print(f"Scraping {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    content_div = soup.find("div", {"id": "mw-content-text"})
    
    if not content_div:
        print(f"Failed to find main content div for URL: {url}")
        return

    for sup in content_div.find_all("sup", class_="reference"):
        sup.decompose()
    for reflist in content_div.find_all(class_="reflist"):
        reflist.decompose()

    paragraphs = content_div.find_all("p")
    clean_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    doc = Document(page_content=clean_text, metadata={"source": url})

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    splitted_docs = text_splitter.split_documents([doc])
    vectorDB.add_documents(splitted_docs)
    print(f"-> Ingested {len(splitted_docs)} chunks from URL.")


def process_documents(directory_path, vectorDB):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created '{directory_path}'")
        return

    raw_docs = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                doc = Document(page_content=text, metadata={"source": filename})
                raw_docs.append(doc)

    if not raw_docs:
        print(f"No .txt files found in {directory_path}.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    splitted_docs = text_splitter.split_documents(raw_docs)
    vectorDB.add_documents(splitted_docs)


if __name__ == "__main__":
    db = get_vector_db()
    
    # for u in urls:
    #     ingest_url(u, db)
        
    # process_documents(directory_path, db)
    
    print("\nAll ingestion tasks completed. The UI will instantly reflect these updates.")