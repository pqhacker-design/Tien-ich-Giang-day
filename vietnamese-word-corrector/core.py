import threading
from word_processor import WordProcessor
from ai import AICorrector

class CoreController:
    def __init__(self, api_key):
        self.processor = WordProcessor()
        self.ai_corrector = AICorrector(api_key)

    def process_file_async(self, file_path, progress_callback, success_callback):
        """Khởi chạy tiến trình ngầm phân tích văn bản"""
        def run():
            try:
                progress_callback(0.1, "Đang đọc cấu trúc file Word...")
                doc = self.processor.load_document(file_path)
                full_text = self.processor.extract_full_text(doc)
                
                progress_bar_val = 0.3
                progress_callback(progress_bar_val, "Đang phân tích ngữ cảnh câu và quét lỗi qua Gemini AI...")
                
                # Chia nhỏ đoạn văn bản nếu file quá dài (>500 trang) để tránh tràn token AI
                text_blocks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
                all_errors = []
                
                for idx, block in enumerate(text_blocks):
                    errors = self.ai_corrector.analyze_text_block(block)
                    all_errors.extend(errors)
                    # Cập nhật thanh tiến trình tịnh tiến dựa trên số khối văn bản
                    step = 0.5 / len(text_blocks)
                    progress_bar_val += step
                    progress_callback(min(progress_bar_val, 0.85), f"Đang quét lỗi đoạn văn bản {idx+1}/{len(text_blocks)}...")
                
                progress_callback(1.0, "Quét lỗi hoàn tất!")
                success_callback(doc, all_errors)
            except Exception as e:
                progress_callback(0.0, f"Lỗi hệ thống: {str(e)}")

        threading.Thread(target=run, daemon=True).start()