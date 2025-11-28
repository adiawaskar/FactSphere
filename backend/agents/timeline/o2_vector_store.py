# # agents/timeline/o2_vector_store.py
# import chromadb
# import numpy as np
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from sentence_transformers import SentenceTransformer
# from typing import List, Dict
# from .config import CONSOLE, CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME, DISTANCE_THRESHOLD

# # --- Lazy Initialization ---
# _client = None
# _collection = None
# embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# def get_collection():
#     """
#     Initializes a persistent ChromaDB client if it hasn't been already.
#     """
#     global _client, _collection
#     if _collection is None:
#         CONSOLE.print("[grey50]   - Initializing ChromaDB client for the first time...[/grey50]")
#         _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
#         _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
#     return _collection

# def chunk_text(article: Dict) -> List[Dict]:
#     """Chunks the article content and attaches metadata to each chunk."""
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=150,
#         length_function=len
#     )
#     chunks = text_splitter.split_text(article['content'])
    
#     chunk_list = []
#     for i, chunk_text in enumerate(chunks):
#         # --- FIX: Sanitize Metadata (ChromaDB crashes on None) ---
#         # We use .get() and 'or "Unknown..."' to ensure we never pass None.
#         meta_url = article.get('url') or "Unknown URL"
#         meta_title = article.get('title') or "Unknown Title"
#         meta_date = article.get('published_date') or "Unknown Date"
#         meta_source = article.get('source') or "Unknown Source"
        
#         chunk_list.append({
#             "text": chunk_text,
#             "metadata": {
#                 "source_url": meta_url,
#                 "title": meta_title,
#                 "pub_date": meta_date,
#                 "publisher": meta_source,
#                 "chunk_id": f"{meta_url}-{i}"
#             }
#         })
#     return chunk_list

# def add_chunks_to_db(chunks: List[Dict]):
#     """
#     Computes embeddings, checks for similarity, and adds unique chunks to ChromaDB.
#     """
#     collection = get_collection()

#     CONSOLE.print(f"\n[yellow]📚 Processing {len(chunks)} chunks for Vector DB...[/yellow]")
#     chunks_to_add = []
    
#     for chunk in chunks:
#         query_embedding = embedding_model.encode(chunk['text']).tolist()
        
#         results = collection.query(
#             query_embeddings=[query_embedding],
#             n_results=1
#         )

#         distances_for_first_query = results['distances'][0]

#         if distances_for_first_query:
#             closest_distance = distances_for_first_query[0]
            
#             if closest_distance < DISTANCE_THRESHOLD:
#                 CONSOLE.print(f"[grey50]    - Skipping similar chunk (distance: {closest_distance:.4f}).[/grey50]")
#                 continue
        
#         chunks_to_add.append(chunk)

#     if not chunks_to_add:
#         CONSOLE.print("[green]   --> No new unique chunks to add.[/green]")
#         return

#     collection.add(
#         documents=[chunk['text'] for chunk in chunks_to_add],
#         metadatas=[chunk['metadata'] for chunk in chunks_to_add],
#         ids=[chunk['metadata']['chunk_id'] for chunk in chunks_to_add]
#     )
#     CONSOLE.print(f"[green]   --> Added {len(chunks_to_add)} new unique chunks to ChromaDB.[/green]")

# def get_all_chunks_from_db() -> List[Dict]:
#     """Retrieves all documents and their metadata from the collection."""
#     collection = get_collection()
    
#     # Safely get data, returning empty list if the database is empty.
#     data = collection.get(include=["metadatas", "documents"])
#     all_chunks = []
    
#     # Handle case where IDs might be None or empty
#     if not data or not data.get('ids'):
#         return []

#     for i in range(len(data['ids'])):
#         all_chunks.append({
#             "text": data['documents'][i],
#             "metadata": data['metadatas'][i]
#         })
#     return all_chunks

# agents/timeline/o2_vector_store.py
import chromadb
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from .config import CONSOLE, CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME, DISTANCE_THRESHOLD

# --- Lazy Initialization ---
_client = None
_collection = None
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_collection():
    """
    Initializes a persistent ChromaDB client if it hasn't been already.
    """
    global _client, _collection
    if _collection is None:
        CONSOLE.print("[grey50]   - Initializing ChromaDB client for the first time...[/grey50]")
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection

def reset_db_client():
    """
    Resets the global ChromaDB client. 
    Must be called before deleting the database directory to release file locks.
    """
    global _client, _collection
    _client = None
    _collection = None
    CONSOLE.print("[grey50]   - ChromaDB client connection reset.[/grey50]")

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
        # --- FIX: Sanitize Metadata (ChromaDB crashes on None) ---
        # We use .get() and 'or "Unknown..."' to ensure we never pass None.
        meta_url = article.get('url') or "Unknown URL"
        meta_title = article.get('title') or "Unknown Title"
        meta_date = article.get('published_date') or "Unknown Date"
        meta_source = article.get('source') or "Unknown Source"
        
        chunk_list.append({
            "text": chunk_text,
            "metadata": {
                "source_url": meta_url,
                "title": meta_title,
                "pub_date": meta_date,
                "publisher": meta_source,
                "chunk_id": f"{meta_url}-{i}"
            }
        })
    return chunk_list

def add_chunks_to_db(chunks: List[Dict]):
    """
    Computes embeddings, checks for similarity, and adds unique chunks to ChromaDB.
    """
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
    collection = get_collection()
    
    # Safely get data, returning empty list if the database is empty.
    data = collection.get(include=["metadatas", "documents"])
    all_chunks = []
    
    # Handle case where IDs might be None or empty
    if not data or not data.get('ids'):
        return []

    for i in range(len(data['ids'])):
        all_chunks.append({
            "text": data['documents'][i],
            "metadata": data['metadatas'][i]
        })
    return all_chunks