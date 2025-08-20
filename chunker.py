import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

# --- 1. Read the content from the text file ---
try:
    with open("content.txt", "r", encoding="utf-8") as f:
        content = f.read()
    print("Successfully loaded content.txt")
except FileNotFoundError:
    print("Error: content.txt not found. Please create this file and add some text to it.")
    exit()

# --- 2. Recursive Text Splitting ---
print("Splitting text into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False,
)
chunks = text_splitter.split_text(content)
print(f"Created {len(chunks)} chunks of text.")

# --- 3. Embed the Chunks ---
print("Loading embedding model and creating embeddings...")
# It is recommended to use models from Hugging Face's Sentence Transformers library. [1, 2]
# For a list of available pre-trained models, you can refer to:
# https://huggingface.co/sentence-transformers
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(chunks)
print("Embeddings created successfully.")

# --- 4. Store in Local ChromaDB ---
print("Storing chunks and embeddings in ChromaDB...")

# Initialize ChromaDB client. By default, it runs in-memory.
# To persist the database, you can specify a path.
# For more details: https://docs.trychroma.com/getting-started
client = chromadb.Client()

# Create a collection. If the collection already exists, you can retrieve it.
# The default embedding function for ChromaDB is all-MiniLM-L6-v2,
# which is the same one we are using from sentence-transformers.
collection_name = "my_text_collection"
if collection_name in [c.name for c in client.list_collections()]:
    client.delete_collection(name=collection_name)

collection = client.create_collection(name=collection_name)

# Generate unique IDs for each chunk
chunk_ids = [str(i) for i in range(len(chunks))]

# Add the chunks, their embeddings, and IDs to the collection. [6]
collection.add(
    embeddings=embeddings.tolist(),  # ChromaDB expects a list of lists for embeddings
    documents=chunks,
    ids=chunk_ids
)

print(f"Successfully stored {collection.count()} items in the '{collection_name}' collection.")

# --- Verification (Optional) ---
# You can query the collection to see if the data has been stored correctly.
print("\n--- Verification ---")
results = collection.query(
    query_texts=["What is the main topic of the document?"],
    n_results=2
)
print("Query results:")
for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
    print(f"Result {i+1}:")
    print(f"  Distance: {dist:.4f}")
    print(f"  Document: {doc[:100]}...")