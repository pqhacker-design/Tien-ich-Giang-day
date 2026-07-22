from google import genai
import json
import streamlit as st
import re

def analyze_document_with_ai(full_text, filename):
    # Prompt chuyên sâu được nhúng trực tiếp vào đây
    prompt = f"""
# VAI TRÒ
Bạn là "AI Chuyên gia Kiểm tra Chính tả và Ngữ pháp Tiếng Việt", có kiến thức chuyên sâu về:
- Chính tả tiếng Việt theo quy định hiện hành.
- Quy tắc viết hoa (NĐ 30/2020/NĐ-CP).
- Dấu câu, Ngữ pháp, Phong cách hành chính, Văn bản giáo dục, GDPT 2018.

Nhiệm vụ duy nhất của bạn là PHÁT HIỆN tất cả lỗi có thể có. KHÔNG viết lại toàn bộ văn bản.

# CÁC LOẠI LỖI CẦN PHÁT HIỆN (Thực hiện qua 3 lượt quét: Chính tả -> Ngữ pháp -> Ngữ nghĩa & Nhất quán):
1. Chính tả (dấu hỏi/ngã, s/x, tr/ch, d/r/gi, i/y, c/k/q, g/gh, ng/ngh, sai/thiếu/thừa ký tự...)
2. Viết hoa (Tên riêng, cơ quan, trường học, địa phương, môn học, nghị định, thông tư, đầu câu...)
3. Khoảng trắng (thừa/thiếu khoảng trắng xung quanh dấu câu, dấu ngoặc...)
4. Dấu câu (thừa/thiếu, sai vị trí dấu chấm, phẩy, hai chấm...)
5. Từ lặp, Từ sai ngữ cảnh, Lỗi từ Hán Việt
6. Viết tắt (THCS, THPT, UBND, GDĐT...)
7. Thuật ngữ giáo dục (Thông tư, Nghị định, KHBD, GDPT 2018, YCCĐ...)
8. Ngữ pháp & Dùng từ

# MỨC ĐỘ LỖI:
- "Cao" (🔴 Nghiêm trọng)
- "Trung bình" (🟠 Trung bình)
- "Thấp" (🟢 Nhẹ)
- "Nghi ngờ" (⚪ Nghi ngờ)

# YÊU CẦU ĐẦU RA:
Hãy trả về duy nhất một chuỗi JSON chuẩn (không kèm văn bản dẫn dắt hay định dạng markdown bên ngoài) theo cấu trúc sau:

{{
   "loai_ho_so": "Hồ sơ Giáo dục / Văn bản Hành chính",
   "do_tin_cay": 95,
   "diem": {{
      "the_thuc": 85,
      "noi_dung": 85,
      "gdpt_2018": 80,
      "nang_luc_so": 80,
      "khoa_hoc": 80,
      "tong": 82
   }},
   "xep_loai": "Khá",
   "thieu_sot_cau_truc": [],
   "gdpt_2018_check": {{
      "pham_chat": "Đạt",
      "nang_luc_chung": "Đạt",
      "nang_luc_dac_thu": "Đạt"
   }},
   "de_xuat_cai_tien": [
      "Kiểm tra lại danh sách các lỗi chính tả và khoảng trắng đã được phát hiện"
   ],
   "loi_the_thuc": [
      {{
         "stt": 1,
         "loai": "Chính tả (Hỏi/Ngã)",
         "goc": "sữa chữa",
         "de_xuat": "sửa chữa",
         "muc_do": "Cao"
      }},
      {{
         "stt": 2,
         "loai": "Dấu câu & Khoảng trắng",
         "goc": "kế hoạch ,",
         "de_xuat": "kế hoạch,",
         "muc_do": "Trung bình"
      }},
      {{
         "stt": 3,
         "loai": "Viết hoa",
         "goc": "bộ giáo dục và đào tạo",
         "de_xuat": "Bộ Giáo dục và Đào tạo",
         "muc_do": "Cao"
      }}
   ]
}}

# ĐẦU VÀO VĂN BẢN (File: {filename}):
{full_text[:4000]}
"""
    
    res = get_ai_response(prompt)
    if res:
        try:
            # Trích xuất JSON từ phản hồi của Gemini
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            st.error(f"⚠️ Lỗi phân tích dữ liệu JSON từ AI: {str(e)}")
            
    # Kết quả dự phòng an toàn nếu gặp sự cố kết nối
    return {
        "loai_ho_so": "Văn bản Giáo dục / Hành chính",
        "do_tin_cay": 80,
        "diem": {"the_thuc": 80, "noi_dung": 80, "gdpt_2018": 80, "nang_luc_so": 80, "khoa_hoc": 80, "tong": 80},
        "xep_loai": "Chưa đánh giá",
        "thieu_sot_cau_truc": [],
        "gdpt_2018_check": {},
        "de_xuat_cai_tien": ["Kiểm tra lại kết nối mạng hoặc API Key"],
        "loi_the_thuc": []
    }
