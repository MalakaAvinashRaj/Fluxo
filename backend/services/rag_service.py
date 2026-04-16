from typing import List
import chromadb  
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction  


client = chromadb.PersistentClient(path = "./chroma_db")
collection = client.get_or_create_collection(name = "flutter_knowledge", embedding_function = SentenceTransformerEmbeddingFunction(model_name = "all-MiniLM-L6-v2", device = "cpu",normalize_embeddings = False),)

def index(documents: List[str], ids: List[str]) -> List[str]:
    collection.upsert( ids = ids, documents = documents)
    return collection

def retrieve(query: str, top_k: int = 5) -> List[str]:
    results = collection.query(query_texts = [query], n_results = top_k)
    return results["documents"][0]

