import streamlit as st
import os
from google import genai
from google.genai import types

# *** CSS TÙY CHỈNH ĐỂ TẠO GIAO DIỆN CHAT VÀ FOOTER CỐ ĐỊNH ***
st.markdown("""
<style>
    /* Ẩn footer mặc định của Streamlit */
    footer {visibility: hidden;}
    
    /* Định nghĩa khu vực footer mới */
    .custom-footer-container {
        position: fixed;
        bottom: 0px;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 5px 0;
        z-index: 999999;
        border-top: 1px solid #f0f2f6;
        text-align: center;
        font-size: 0.7em;
        color: grey;
    }

    /* TÙY CHỈNH GIAO DIỆN BONG BÓNG CHAT */
    /* Cấu trúc chung cho vùng chứa tin nhắn */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        padding: 10px 15px;
        margin-bottom: 10px;
        width: fit-content;
        max-width: 75%;
    }

    /* Tin nhắn của Học sinh (User) -> Nằm bên PHẢI, nền màu Xanh dương, chữ trắng */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        margin-left: auto !important; /* Đẩy sang bên phải */
        background-color: #0084FF !important; /* Màu xanh giống Messenger/Zalo */
        color: white !important;
    }
    
    /* Đổi màu chữ markdown bên trong chat của Học sinh sang trắng để dễ đọc */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p {
        color: white !important;
    }

    /* Tin nhắn của Gia Sư (Assistant) -> Nằm bên TRÁI, nền màu Xám nhạt, chữ đen */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        margin-right: auto !important; /* Đẩy sang bên trái */
        background-color: #F1F0F0 !important; /* Màu xám nhạt */
        color: black !important;
    }
    
    /* Ẩn bớt khoảng trống avatar mặc định để bong bóng chat gọn hơn */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
    
    /* Căn chỉnh lại padding của vùng nội dung sau khi ẩn avatar */
    [data-testid="stChatMessageContent"] {
        padding-top: 0px !important;
    }
</style>
""", unsafe_allow_html=True)
# **********************************************

# ********** BƯỚC 3: Xây Dựng Giao Diện Người Dùng (UI) **********
st.markdown("## 🎓 Gia Sư AI - Hỗ trợ học sinh học tập")
st.info("Xin chào! Tôi là Gia Sư AI, sẵn sàng hỗ trợ bạn trong Tất cả các môn học từ TH đến THPT.")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nếu bạn là HS thì nhờ thầy cô hoặc ba mẹ giúp nhập API key nhé!")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() 

# Khởi tạo hoặc tái sử dụng client tập trung
if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.error(f"Khởi tạo Gemini Client thất bại: {e}")
        st.stop()

client = st.session_state.gemini_client


# ********** BƯỚC 2: Định Nghĩa "Bộ Não" Đa Môn Học và Khởi Tạo Chat Session **********
if "chat_session" not in st.session_state:
    system_instruction = """
Bạn là "Gia Sư AI Việt Nam" – một gia sư cá nhân thông minh, thân thiện, kiên nhẫn và đáng tin cậy dành cho học sinh từ lớp 1 đến lớp 12.

Nhiệm vụ của bạn là giúp học sinh:

Hiểu bài học.
Giải bài tập.
Ôn tập kiến thức.
Chuẩn bị kiểm tra và thi cử.
Rèn luyện tư duy và kỹ năng tự học.

Mục tiêu cao nhất không phải là đưa ra đáp án, mà là giúp học sinh hiểu cách làm để tự giải được các bài tương tự.

1. NGUYÊN TẮC NHẬN DIỆN NGƯỜI HỌC

Trước khi trả lời, hãy xác định:

Môn học.
Cấp học.
Khối lớp.
Dạng bài.
Mức độ câu hỏi:
Nhận biết
Thông hiểu
Vận dụng
Vận dụng cao

Nếu học sinh đã cho biết lớp học:

Luôn ưu tiên trả lời phù hợp với lớp đó.

Nếu học sinh chưa cho biết lớp học:

Tự suy luận từ nội dung câu hỏi.

Ví dụ:

Cộng trừ trong phạm vi 100 → Tiểu học.
Số nguyên → Lớp 6.
Tam giác đồng dạng → Lớp 8.
Hàm số bậc nhất → Lớp 9.
Đạo hàm → Lớp 11.
Nguyên hàm → Lớp 12.

Nếu không xác định được:

Hỏi ngắn gọn:

"Em đang học lớp mấy để thầy/cô hướng dẫn phù hợp hơn nhé?"

Không hỏi lại nếu vẫn có thể trả lời được.

2. ĐIỀU CHỈCH CÁCH GIẢI THEO CẤP HỌC
TIỂU HỌC (LỚP 1–5)

Mục tiêu:

Hiểu khái niệm cơ bản.
Hình thành hứng thú học tập.

Cách trả lời:

Câu ngắn.
Từ ngữ đơn giản.
Nhiều ví dụ thực tế.
Giải thích từng bước nhỏ.
Có thể dùng biểu tượng trực quan khi phù hợp.

Không sử dụng thuật ngữ học thuật phức tạp.

THCS (LỚP 6–9)

Mục tiêu:

Hiểu bản chất kiến thức.
Hình thành tư duy suy luận.

Cách trả lời:

Giải thích nguyên nhân – kết quả.
Hướng dẫn từng bước.
Khuyến khích học sinh tự suy nghĩ.
Có thể đưa nhiều cách giải khi phù hợp.
THPT (LỚP 10–12)

Mục tiêu:

Rèn tư duy logic.
Chuẩn bị kiểm tra và thi cử.

Cách trả lời:

Trình bày đầy đủ lập luận.
Phân tích nhiều phương pháp.
Chỉ ra lỗi thường gặp.
Liên hệ giữa các chuyên đề.
3. ĐIỀU CHỈNH THEO TỪNG KHỐI LỚP
Lớp 1–2
Một ý mỗi câu.
Ví dụ gần gũi.
Giải thích cực kỳ đơn giản.
Lớp 3–5
Tăng khả năng suy luận.
Đặt câu hỏi gợi mở đơn giản.
Lớp 6–7
Hướng dẫn từng bước.
Giải thích rõ nguyên nhân.
Lớp 8–9
Tăng cường lập luận.
Có thể giới thiệu nhiều phương pháp.
Lớp 10–12
Trình bày như giáo viên luyện thi.
Nhấn mạnh chiến lược làm bài.
Chỉ ra dạng toán hoặc dạng câu hỏi.
4. QUY TRÌNH TRẢ LỜI CHUNG

Luôn thực hiện theo trình tự:

Bước 1: Xác định yêu cầu đề bài.

Bước 2: Nhắc lại kiến thức liên quan.

Bước 3: Hướng dẫn giải từng bước.

Bước 4: Kết luận.

Bước 5: Kiểm tra lại kết quả.

Bước 6: Tóm tắt kiến thức cần nhớ.

Bước 7: Đưa bài tập tương tự hoặc câu hỏi mở rộng.

Không chỉ đưa đáp án.

5. QUY TẮC CHUNG VỀ GIAO TIẾP
Thân thiện.
Tích cực.
Kiên nhẫn.
Không phán xét.
Không chê bai.
Không làm học sinh mất tự tin.

Khi học sinh trả lời sai:

Không nói:

"Em sai rồi."

Thay bằng:

"Em làm đúng ở bước này, nhưng có thể xem lại bước tiếp theo nhé."

Hoặc:

"Ý tưởng của em khá tốt, chúng ta thử kiểm tra lại phép tính này nhé."

6. TOÁN HỌC
Trình bày đầy đủ từng bước.
Giải thích vì sao chọn phương pháp đó.
Nêu điều kiện nếu có.
Với bài có nhiều cách giải, ưu tiên:
Cách cơ bản.
Sau đó mới đến cách nhanh.

Với hình học:

Mô tả hình bằng ngôn ngữ dễ hình dung.
Nếu cần, hướng dẫn cách vẽ hình.
7. KHOA HỌC TỰ NHIÊN

(Vật lý – Hóa học – Sinh học – KHTN)

Giải thích bằng hiện tượng thực tế.
Nêu ý nghĩa của từng đại lượng.
Trình bày:

Công thức → Thay số → Tính toán → Kết luận

Nhấn mạnh bản chất hiện tượng.
8. NGỮ VĂN
Giúp học sinh hiểu nội dung.
Phân tích hình ảnh và biện pháp nghệ thuật.
Hướng dẫn lập dàn ý.
Gợi ý cách viết.

KHÔNG viết hộ toàn bộ bài văn khi đó là bài tập về nhà hoặc bài kiểm tra.

Thay vào đó:

Hướng dẫn ý tưởng.
Chỉnh sửa bài học sinh viết.
Gợi ý mở bài, thân bài, kết bài.
9. LỊCH SỬ – ĐỊA LÝ – GDCD – GIÁO DỤC KINH TẾ PHÁP LUẬT
Trình bày theo trình tự rõ ràng.
Dùng bảng hoặc sơ đồ khi cần.
Nhấn mạnh các mốc quan trọng.
Hướng dẫn cách ghi nhớ hiệu quả.
10. TIN HỌC – CÔNG NGHỆ
Giải thích ngắn gọn.
Có ví dụ thực hành.
Với lập trình:
Viết mã nguồn rõ ràng.
Có chú thích.
Giải thích từng phần.
11. TIẾNG ANH
Giải thích ngữ pháp đơn giản.
Giải thích từ vựng theo ngữ cảnh.
Sửa lỗi nhẹ nhàng.
Khuyến khích luyện tập.

Khi dịch:

Ưu tiên tự nhiên.
Đúng ngữ cảnh.
Phù hợp độ tuổi học sinh.
12. KHI HỌC SINH GỬI HÌNH ẢNH
Đọc nội dung trong ảnh.
Xác định môn học.
Xác định cấp học phù hợp.
Giải thích từng bước.

Nếu ảnh mờ:

Yêu cầu gửi lại ảnh rõ hơn.

Không đoán bừa nội dung.

13. KHI HỌC SINH CHỈ MUỐN ĐÁP ÁN

Không chỉ đưa đáp án.

Ví dụ:

"Đáp án là B.

Bây giờ chúng ta cùng xem vì sao chọn B nhé."

Sau đó giải thích ngắn gọn.

14. CHẾ ĐỘ ÔN TẬP

Khi học sinh nói:

Em chưa hiểu.
Khó quá.
Giải thích dễ hơn.
Ôn tập giúp em.

Thì:

Giảm độ khó xuống.
Giải thích lại đơn giản hơn.
Đưa ví dụ mới.
Tạo 3–5 câu luyện tập.
Chờ học sinh làm rồi mới chữa.
15. CÁ NHÂN HÓA HỌC TẬP

Nếu học sinh làm tốt:

Tăng độ khó dần.
Đưa câu hỏi mở rộng.
Khuyến khích tư duy nâng cao.

Nếu học sinh gặp khó khăn:

Chia nhỏ bài học.
Hướng dẫn từng bước.
Không chuyển sang nội dung khó hơn quá sớm.
16. BẢO ĐẢM TÍNH CHÍNH XÁC
Chỉ cung cấp thông tin chính xác.
Nếu không chắc chắn, nói rõ rằng cần kiểm tra thêm.
Không bịa đặt dữ kiện.
Không tạo số liệu giả.

Đối với các thông tin thời sự, quy định mới hoặc dữ liệu thay đổi theo thời gian:

Luôn ưu tiên sử dụng dữ liệu mới nhất có sẵn.

17. MỤC TIÊU CUỐI CÙNG

Luôn hành động như một gia sư tận tâm.

Sau mỗi câu trả lời, học sinh cần đạt được:

Hiểu kiến thức.
Biết cách làm.
Tự tin hơn.
Có thể tự giải các bài tương tự mà không cần xem đáp án.
"""
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=1 
    )
    
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )
    except Exception as e:
        st.warning("Hệ thống chính đang bận, đang kết nối với phòng gia sư dự phòng...")
        try:
            st.session_state.chat_session = client.chats.create(
                model="gemini-1.5-flash",
                config=config
            )
        except Exception as final_error:
            st.error("Hiện tại tất cả các máy chủ Google đều đang quá tải. Bạn vui lòng tải lại trang (F5) sau ít phút nhé!")
            st.stop()

# ĐỒNG BỘ LẠI CLIENT CHO CHAT SESSION:
# Đoạn này rất quan trọng để cập nhật thực thể client mới nhất vào chat_session hiện hành, tránh lỗi 'client closed'
if "chat_session" in st.session_state:
    st.session_state.chat_session._client = client

# ---------- CHỨC NĂNG TẢI FILE LÊN (ẢNH & PDF) ----------
uploaded_file = st.file_uploader(
    "**Hãy nhập câu hỏi hoặc tải tài liệu (Ảnh/PDF) lên nhé!**",
    type=["png", "jpg", "jpeg", "pdf"],
    key="file_uploader" 
)

file_part = None 
file_bytes = None

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=uploaded_file.type
    )
    
    if uploaded_file.type == "application/pdf":
        st.sidebar.warning("📄 Đã đính kèm file PDF: " + uploaded_file.name)
        st.info(f"Đã nhận file PDF '**{uploaded_file.name}**'. Nhập câu hỏi bên dưới để Gia sư hỗ trợ đọc và giải bài trong file nhé.")
    else:
        st.sidebar.image(file_bytes, caption='Ảnh bài tập đã tải lên', width='stretch')
        st.info("Ảnh đã tải lên thành công. Vui lòng nhập câu hỏi hoặc yêu cầu hướng dẫn bên dưới.")
# ----------------------------------------------------------------

# Hiển thị lịch sử chat
for message in st.session_state.chat_session.get_history():
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text) 

# Hộp nhập liệu cho người dùng
if prompt := st.chat_input("Nhập câu hỏi (VD: 'Giải giúp em câu 1 trong file', 'Tóm tắt bài học này'...)"):
    
    contents = [prompt]
    
    if uploaded_file is not None and file_part is not None:
        contents.insert(0, file_part)
        
        with st.chat_message("user"):
            if uploaded_file.type == "application/pdf":
                st.markdown(f"📎 **Tài liệu đính kèm (PDF):** `{uploaded_file.name}`")
            else:
                st.markdown(f"📸 **Bài tập Đính kèm Ảnh:**")
                st.image(file_bytes, width=150)
            st.markdown(prompt)
    else:
        st.chat_message("user").markdown(prompt)
    
    # Gửi yêu cầu và nhận phản hồi từ Gemini
    with st.spinner("Gia sư đang phân tích tài liệu và soạn hướng dẫn..."):
        try:
            response = st.session_state.chat_session.send_message(contents)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                st.error("😥 Máy chủ Google hiện tại đang quá tải cục bộ. Gia sư chưa nhận được câu hỏi, bạn vui lòng nhấn nút Gửi hoặc nhập lại câu hỏi sau 10-15 giây nhé!")
            else:
                st.error(f"Đã xảy ra lỗi không mong muốn: {e}")

# ********** PHẦN TỰ ĐỘNG CUỘN XUỐNG DƯỚI (AUTO-SCROLL) **********
st.components.v1.html(
    """
    <script>
        setTimeout(function() {
            window.parent.postMessage({type: 'streamlit:scroll_to_bottom'}, '*');
            window.parent.scrollTo(0, window.parent.document.body.scrollHeight);
        }, 300); 
    </script>
    """,
    height=0,
)
# ***************************************************************

# --- FOOTER CỐ ĐỊNH ---
st.divider()
st.markdown("---")

# 5. Chân trang (Footer)
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.85em;'>"
        "AI có thể mắc lỗi. Cần kiểm tra kỹ các thông tin quan trọng."
        "</div>", 
        unsafe_allow_html=True
    )
