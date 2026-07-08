import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import streamlit as st

class KnowledgeHubRAG:
    def __init__(self, persist_directory: str, api_key: str):
        self.persist_directory = persist_directory
        self.api_key = api_key
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        ) if self.api_key else None
        
        if self.embeddings:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="edu_knowledge_base"
            )
        else:
            self.vector_store = None

    def add_document(self, text: str, metadata: dict):
        if not self.vector_store:
            return False
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_text(text)
        docs = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
        self.vector_store.add_documents(docs)
        self.vector_store.persist()
        return True

    def query_relevant_context(self, query: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        try:
            results = self.vector_store.similarity_search(query, k=k)
            context = "\n---\n".join([f"[Nguồn: {doc.metadata.get('source', 'VB Pháp lý')}]:\n{doc.page_content}" for doc in results])
            return context
        except Exception:
            return ""
