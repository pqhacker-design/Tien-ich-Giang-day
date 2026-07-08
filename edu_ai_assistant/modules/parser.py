import docx
import pypdf
import io
from typing import Tuple, Dict, Any

class DocumentParser:
    @staticmethod
    def parse_file(uploaded_file) -> Tuple[str, Dict[str, Any]]:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        content = ""
        metadata = {
            "file_name": uploaded_file.name,
            "file_size_kb": round(uploaded_file.size / 1024, 2),
            "page_count": 0,
            "word_count": 0,
            "char_count": 0
        }

        if file_extension == "docx":
            doc = docx.Document(uploaded_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n".join(paragraphs)
            metadata["page_count"] = max(1, len(paragraphs) // 15)
        elif file_extension == "pdf":
            pdf_reader = pypdf.PdfReader(uploaded_file)
            metadata["page_count"] = len(pdf_reader.pages)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        elif file_extension in ["txt", "md"]:
            content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            metadata["page_count"] = max(1, len(content) // 2000)
        else:
            raise ValueError(f"Định dạng .{file_extension} chưa được hỗ trợ.")

        metadata["word_count"] = len(content.split())
        metadata["char_count"] = len(content)
        return content, metadata
