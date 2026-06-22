import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class RAGManager:
    def __init__(self):
        # Khởi tạo mô hình nhúng đa ngôn ngữ tối ưu cho tiếng Việt
        self.encoder = SentenceTransformer("symanto/sn-xlm-roberta-base-snli-mnli-anli-xnli")
        self.dimension = 768
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

    def add_document_to_library(self, text: str, doc_name: str):
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]
        if not paragraphs: return
        embeddings = self.encoder.encode(paragraphs)
        self.index.add(np.array(embeddings).astype('float32'))
        for p in paragraphs:
            self.metadata.append({"doc_name": doc_name, "text": p})

    def search_similar_style(self, query: str, top_k: int = 2) -> list:
        if self.index.ntotal == 0:
            return []
        query_vector = self.encoder.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.metadata) and idx != -1:
                results.append(self.metadata[idx])
        return results
