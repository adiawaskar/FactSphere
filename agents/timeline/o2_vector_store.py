# agents/timeline/02_vector_store.py
import chromadb
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from config import CONSOLE, CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME, DISTANCE_THRESHOLD

# --- MODIFIED SECTION: Lazy Initialization ---

# 1. Define global variables for the client and collection, initially set to None.
#    This prevents the database file from being locked when the module is imported.
_client = None
_collection = None
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME) # The embedding model is safe to load once.

# 2. Create a function to initialize the DB on first use and return the collection object.
def get_collection():
    """
    Initializes a persistent ChromaDB client if it hasn't been already,
    and returns the collection object. This is a singleton pattern.
    """
    global _client, _collection
    if _collection is None:
        # This code will only run once, the first time a function needs the database.
        # By this point, the cleanup script in main.py will have already run.
        CONSOLE.print("[grey50]   - Initializing ChromaDB client for the first time...[/grey50]")
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection

# --- END OF MODIFIED SECTION ---


def chunk_text(article: Dict) -> List[Dict]:
    """Chunks the article content and attaches metadata to each chunk."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_text(article['content'])
    
    chunk_list = []
    for i, chunk_text in enumerate(chunks):
        chunk_list.append({
            "text": chunk_text,
            "metadata": {
                "source_url": article['url'],
                "title": article['title'],
                "pub_date": article['published_date'],
                "publisher": article['source'],
                "chunk_id": f"{article['url']}-{i}"
            }
        })
    return chunk_list

def add_chunks_to_db(chunks: List[Dict]):
    """
    Computes embeddings, checks for similarity, and adds unique chunks to ChromaDB.
    """
    # Get the collection object using our new function instead of the old global variable.
    collection = get_collection()

    CONSOLE.print(f"\n[yellow]📚 Processing {len(chunks)} chunks for Vector DB...[/yellow]")
    chunks_to_add = []
    
    for chunk in chunks:
        query_embedding = embedding_model.encode(chunk['text']).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        distances_for_first_query = results['distances'][0]

        if distances_for_first_query:
            closest_distance = distances_for_first_query[0]
            
            if closest_distance < DISTANCE_THRESHOLD:
                CONSOLE.print(f"[grey50]    - Skipping similar chunk (distance: {closest_distance:.4f}).[/grey50]")
                continue
        
        chunks_to_add.append(chunk)

    if not chunks_to_add:
        CONSOLE.print("[green]   --> No new unique chunks to add.[/green]")
        return

    collection.add(
        documents=[chunk['text'] for chunk in chunks_to_add],
        metadatas=[chunk['metadata'] for chunk in chunks_to_add],
        ids=[chunk['metadata']['chunk_id'] for chunk in chunks_to_add]
    )
    CONSOLE.print(f"[green]   --> Added {len(chunks_to_add)} new unique chunks to ChromaDB.[/green]")

def get_all_chunks_from_db() -> List[Dict]:
    """Retrieves all documents and their metadata from the collection."""
    # Get the collection object using our new function.
    collection = get_collection()
    
    # Safely get data, returning empty list if the database is empty.
    data = collection.get(include=["metadatas", "documents"])
    all_chunks = []
    for i in range(len(data.get('ids', []))):
        all_chunks.append({
            "text": data['documents'][i],
            "metadata": data['metadatas'][i]
        })
    return all_chunks