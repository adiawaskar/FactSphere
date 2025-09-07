# knowledge_base.py
import hashlib
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CONSOLE, CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME

class KnowledgeBase:
    """Manages the ChromaDB vector store for neutral articles."""
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=70)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        CONSOLE.print(f"[green]✅ Knowledge Base initialized at '{CHROMA_DB_PATH}'.[/green]")

    def add_document(self, content: str, source_url: str):
        """Chunks, embeds, and adds a neutral document to the collection."""
        chunks = self.text_splitter.split_text(content)
        if not chunks: return

        # Use hash of first chunk as a simple duplicate check ID
        doc_id = hashlib.md5(chunks[0].encode()).hexdigest()
        if self.collection.get(ids=[doc_id])['ids']:
            CONSOLE.print("[yellow]    Skipping duplicate document.[/yellow]")
            return

        embeddings = self.embedding_model.encode(chunks).tolist()
        # Create unique IDs for each chunk based on the document ID and chunk index
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_url} for _ in chunks]
        
        self.collection.add(embeddings=embeddings, documents=chunks, metadatas=metadatas, ids=chunk_ids)
        CONSOLE.print(f"[green]    --> Added {len(chunks)} chunks to the neutral knowledge base.[/green]")

    def query(self, misconception: str, n_results: int = 5) -> List[str]:
        """Queries the knowledge base for relevant neutral chunks."""
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_embeddings=self.embedding_model.encode([misconception]).tolist(),
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []