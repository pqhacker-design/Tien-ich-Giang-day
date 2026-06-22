class RAGManager:
    def __init__(self):
        self.library = []

    def add_document_to_library(self, text: str, doc_name: str):
        # Lưu trữ thô dạng văn bản gọn nhẹ, không tốn RAM
        self.library.append({"doc_name": doc_name, "text": text})

    def search_similar_style(self, query: str, top_k: int = 1) -> list:
        # Trả về các tài liệu mẫu trong thư viện để AI làm ngữ cảnh đối chiếu
        return self.library[:top_k]
