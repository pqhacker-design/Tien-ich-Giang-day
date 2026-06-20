import streamlit as st
import streamlit.components.v1 as components
import json
from ai_classroom_game.database.db_manager import DatabaseManager
from ai_classroom_game.services.ai_service import AIService
from ai_classroom_game.modules.interactives import render_lucky_wheel
from ai_classroom_game.modules.exporters import DocumentExporter

# 1. Cấu hình trang & Giao diện chuẩn Enterprise
st.set_page_config(page_title="AI Thiết Kế Hoạt Động Lớp Học", layout="wide", initial_sidebar_state="expanded")
db = DatabaseManager()

# Khởi tạo Session State bảo vệ dữ liệu nền
if "generated_quiz" not in st.session_state:
    st.session_state.generated_quiz = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

# Nhúng Custom CSS giao diện tối ưu hóa hiển thị cho máy chiếu trường học
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; padding: 10px 20px; }
    .stTabs [data-baseweb="tab"]:hover { color: #ff4b4b; }
    .stTabs [aria-selected="true"] { background-color: rgba(255,75,75,0.1); border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# 2. THANH THÔNG TIN BỔ TRỢ (SIDEBAR) - CẤU HÌNH TIÊU CHUẨN SƯ PHẠM
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    gemini_key = st.session_state["gemini_api_key"].strip()
else:
    st.warning("⚠️ Vui lòng cấu hình Google Gemini API Key tại **Trang chủ** trước khi vận hành.")
    st.stop()

openai_key = st.session_state.get("openai_api_key", "").strip()

with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/000000/brainstorm-skill.png", width=80)
    st.title("⚙️ CẤU HÌNH HOẠT ĐỘNG")
    st.markdown("---")
    
    subject = st.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "Khoa học tự nhiên", "Lịch sử & Địa lý", "Tin học", "STEM"])
    grade = st.selectbox("Khối lớp", [f"Lớp {i}" for i in range(1, 13)])
    duration = st.slider("Thời lượng hoạt động (Phút)", 5, 45, 15, step=5)
    difficulty = st.select_slider("Mức độ nhận thức", options=["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"])
    organization = st.radio("Hình thức tổ chức", ["Cá nhân", "Cặp đôi", "Hoạt động nhóm", "Toàn lớp"])
    
    st.markdown("---")
    st.success("✔ Đã đồng bộ API Key thành công từ Trang chủ.")

ai_engine = AIService(gemini_key=gemini_key, openai_key=openai_key)

# 3. KHU VỰC ĐIỀU KHIỂN CHÍNH (MAIN DASHBOARD)
st.title("🚀 AI Thiết Kế Hoạt Động Tương Tác Trong Lớp Học")
st.caption("Giải pháp số hóa bài giảng, tạo trò chơi tương tác trực tiếp chuẩn Kahoot/Quizizz cho giáo viên hiện đại.")

tabs = st.tabs([
    "🎯 Khởi Động & Sinh Hoạt Trình", 
    "📘 Thiết Kế Câu Hỏi AI", 
    "🕹️ Trò Chơi Trực Tiếp", 
    "📑 Kịch Bản Sư Phạm", 
    "📦 Xuất Bản Tài Liệu"
])

# --- TAB 1: KHỞI ĐỘNG ---
with tabs[0]:
    st.header("⚡ Tạo Hoạt Động Khởi Động Sinh Động")
    col1, col2 = st.columns([1, 1])
    with col1:
        warmup_type = st.selectbox("Chọn loại trò chơi khởi động nhanh", [
            "Vòng quay may mắn", "Đuổi hình bắt chữ", "Ai nhanh hơn", "Mật mã bí mật", "Lật mảnh ghép"
        ])
        warmup_prompt = st.text_area("Yêu cầu bổ sung cho trò chơi", placeholder="Ví dụ: Thiết kế trò chơi khởi động liên quan đến kiến thức phân số...")
    with col2:
        if st.button("🔥 Tạo Kịch Bản Trò Chơi", type="primary"):
            with st.spinner("AI đang thiết kế cấu trúc trò chơi..."):
                prompt_cmd = f"Tạo kịch bản chi tiết cho trò chơi khởi động '{warmup_type}' dành cho môn {subject}, {grade}. Yêu cầu: {warmup_prompt}. Gồm Luật chơi, Cách tính điểm."
                res = ai_engine.generate_content(prompt_cmd)
                st.success("Tạo thành công!")
                st.markdown(res)

# --- TAB 2: THIẾT KẾ CÂU HỎI AI ---
with tabs[1]:
    st.header("🧠 Hệ Thống Sinh Câu Hỏi Tương Tác Đa Dạng")
    c1, c2 = st.columns([1, 2])
    with c1:
        topic_input = st.text_input("Tên bài học học tập", placeholder="Ví dụ: Định lý Pitago")
        goals_input = st.text_input("Mục tiêu cần đạt", placeholder="Ví dụ: Học sinh vận dụng tính cạnh huyền")
        content_input = st.text_area("Nội dung cốt lõi/Tóm tắt tài liệu", placeholder="Nhập nội dung bài học để AI bám sát...")
        generate_btn = st.button("✨ Kích hoạt Trí Tuệ Nhân Tạo", type="primary")
        
    with c2:
        if generate_btn:
            if not (topic_input and content_input):
                st.warning("Vui lòng nhập đầy đủ Tên bài và Nội dung cốt lõi.")
            else:
                with st.spinner("Hệ thống đang bóc tách nội dung và sinh bộ câu hỏi..."):
                    try:
                        quiz_res = ai_engine.generate_quiz(topic_input, content_input, goals_input)
                        st.session_state.generated_quiz = quiz_res
                        st.session_state.current_topic = topic_input
                        db.save_history(subject, grade, topic_input, "Quiz Tổng Hợp", quiz_res)
                    except Exception as err:
                        st.error(f"Lỗi hệ thống khi phân tích JSON: {err}")
                        
        if st.session_state.generated_quiz:
            st.success(f"Dữ liệu bộ câu hỏi chuẩn hóa cho bài học: {st.session_state.current_topic}")
            q_data = st.session_state.generated_quiz
            
            if "trac_nghiem" in q_data:
                for idx, t in enumerate(q_data["trac_nghiem"]):
                    with st.expander(f"🔹 Câu hỏi trắc nghiệm {idx+1}: {t['cau_hoi']}"):
                        st.write(f"**Các phương án chọn:** {', '.join(t['options'])}")
                        st.info(f"✔ **Đáp án:** {t['dap_an']} | **Giải thích:** {t['giai_thich']}")

# --- TAB 3: TRÒ CHƠI TƯƠNG TÁC TRỰC TIẾP ---
with tabs[2]:
    st.header("🎬 Đấu Trường Tương Tác Thời Gian Thực")
    st.info("💡 Mẹo: Nhấn F11 để toàn màn hình trình duyệt khi chiếu cho học sinh chơi trực tiếp tại lớp.")
    
    game_select = st.selectbox("Lựa chọn Game Engine vận hành", ["Vòng Quay May Mắn", "Ô Chữ Kỳ Diệu", "Ai Là Triệu Phú"])
    
    if st.session_state.generated_quiz and "trac_nghiem" in st.session_state.generated_quiz:
        quiz_source = st.session_state.generated_quiz["trac_nghiem"]
    else:
        quiz_source = [
            {"cau_hoi": "Đâu là hành tinh gần Mặt Trời nhất?", "options": ["Sao Thủy", "Sao Kim", "Trái Đất", "Sao Hỏa"], "dap_an": "Sao Thủy", "giai_thich": "Sao Thủy cách Mặt Trời 58 triệu km."},
            {"cau_hoi": "Số nguyên tố nhỏ nhất là số nào?", "options": ["0", "1", "2", "3"], "dap_an": "2", "giai_thich": "Số 2 là số nguyên tố chẵn duy nhất và nhỏ nhất."},
            {"cau_hoi": "Nước chiếm khoảng bao nhiêu phần trăm bề mặt Trái Đất?", "options": ["50%", "60%", "71%", "85%"], "dap_an": "71%", "giai_thich": "Đại dương và biển bao phủ khoảng 71% bề mặt hành tinh."}
        ]

    if game_select == "Vòng Quay May Mắn":
        col_g1, col_g2 = st.columns([1, 3])
        with col_g1:
            st.markdown("### 📋 Thiết lập phòng đấu")
            students_raw = st.text_area("Danh sách học sinh (Mỗi người một hàng)", "Nguyễn Văn A\nTrần Thị B\nLê Hoàng C\nPhạm Minh D\nĐỗ Hồng E")
            students_list = [s.strip() for s in students_raw.split("\n") if s.strip()]
            q_list = [q['cau_hoi'] for q in quiz_source]
        with col_g2:
            render_lucky_wheel(students_list, q_list)

    elif game_select == "Ô Chữ Kỳ Diệu":
        st.subheader("🧩 Ô Chữ Kiến Thức (Đồng bộ dữ liệu AI)")
        
        if st.session_state.generated_quiz and "o_chu" in st.session_state.generated_quiz:
            crossword_data = st.session_state.generated_quiz["o_chu"]
            st.success(f"✔ Đã nạp thành công ma trận ô chữ AI cho bài: **{st.session_state.current_topic}**")
        else:
            crossword_data = [
                {"hang": 1, "tu_khoa": "TOANHOC", "goi_y": "Môn học nghiên cứu về các số, hình học và cấu trúc?"},
                {"hang": 2, "tu_khoa": "PITAGO", "goi_y": "Định lý toán học nổi tiếng tính cạnh huyền tam giác vuông?"},
                {"hang": 3, "tu_khoa": "GEMINI", "goi_y": "Tên mô hình AI tiên tiến của Google hiện nay?"},
                {"hang": 4, "tu_khoa": "STREAMLIT", "goi_y": "Thư viện Python giúp xây dựng nhanh ứng dụng web này?"}
            ]
        
        js_crossword = json.dumps(crossword_data, ensure_ascii=False)
        
        crossword_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { background: #0e1117; color: white; font-family: sans-serif; text-align: center; }
                .row-container { margin: 12px 0; display: flex; justify-content: center; align-items: center; }
                .hint-btn { background: #262730; color: #fff; border: 1px solid #464855; padding: 8px 15px; cursor: pointer; border-radius: 4px; font-weight: bold; margin-right: 15px; width: 120px; text-align: center; }
                .hint-btn:hover { background: #ff4b4b; border-color: #ff4b4b; }
                .cell { width: 35px; height: 35px; border: 2px solid #464855; display: inline-block; text-align: center; line-height: 35px; font-weight: bold; font-size: 20px; text-transform: uppercase; margin: 2px; background: #1e222b; color: transparent; border-radius: 4px; cursor: pointer; user-select: none; transition: background 0.2s; }
                .cell.reveal { color: #00e676; background: #2e3d30; border-color: #00e676; }
                #hint-display { font-size: 20px; color: #ffeb3b; margin-top: 20px; min-height: 40px; font-style: italic; background: #1a1c24; padding: 10px; border-radius: 6px; display: inline-block; padding-left: 20px; padding-right: 20px; }
            </style>
        </head>
        <body>
            <div id="board"></div>
            <div id="hint-display">💡 Nhấn vào nút tiêu đề hàng bên trái để xem câu hỏi gợi ý!</div>
            <script>
                const data = DATA_PLACEHOLDER;
                const board = document.getElementById('board');
                const hintDisplay = document.getElementById('hint-display');

                data.forEach((item) => {
                    const rowDiv = document.createElement('div');
                    rowDiv.className = 'row-container';
                    
                    const btn = document.createElement('button');
                    btn.className = 'hint-btn';
                    btn.innerText = "Hàng ngang " + item.hang;
                    btn.onclick = () => {
                        hintDisplay.innerText = "❓ Gợi ý dòng " + item.hang + ": " + item.goi_y;
                    };
                    rowDiv.appendChild(btn);
                    
                    for(let i=0; i < item.tu_khoa.length; i++) {
                        const cell = document.createElement('div');
                        cell.className = 'cell';
                        cell.innerText = item.tu_khoa[i];
                        cell.onclick = () => {
                            cell.classList.toggle('reveal');
                        };
                        rowDiv.appendChild(cell);
                    }
                    board.appendChild(rowDiv);
                });
            </script>
        </body>
        </html>
        """.replace("DATA_PLACEHOLDER", js_crossword) # Sử dụng hàm .replace an toàn tuyệt đối cho Python 3.14
        
        components.html(crossword_html, height=480)

    elif game_select == "Ai Là Triệu Phú":
        st.subheader("💰 Đấu Trường: Ai Là Triệu Phú Giáo Khoa")
        js_quiz = json.dumps(quiz_source, ensure_ascii=False)
        
        millionaire_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
            <style>
                body { background: #0c1020; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; padding: 10px; }
                .game-box { max-width: 700px; margin: auto; background: #121830; padding: 25px; border-radius: 12px; border: 2px solid #1e295d; box-shadow: 0 0 20px rgba(0,0,0,0.6); }
                .q-section { font-size: 22px; font-weight: bold; margin-bottom: 25px; background: #1a234a; padding: 15px; border-radius: 8px; border-left: 5px solid #00e676; }
                .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
                .opt-btn { background: #1e295d; color: white; border: 1px solid #3b4da3; padding: 15px; font-size: 18px; border-radius: 30px; cursor: pointer; text-align: left; padding-left: 25px; transition: 0.2s; }
                .opt-btn:hover { background: #2a3b8f; border-color: #00e676; }
                .lifelines { margin-top: 25px; display: flex; justify-content: center; gap: 15px; }
                .life-btn { background: #ff9800; color: black; border: none; padding: 8px 18px; font-weight: bold; border-radius: 20px; cursor: pointer; }
                .life-btn.used { background: #555 !important; color: #888; cursor: not-allowed; text-decoration: line-through; }
                #score-board { font-size: 18px; color: #00e676; margin-bottom: 10px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="game-box">
                <div id="score-board">CÂU HỎI SỐ: 1</div>
                <div class="q-section" id="question-text">Đang tải câu hỏi...</div>
                <div class="options-grid" id="options-box"></div>
                <div class="lifelines">
                    <button class="life-btn" id="btn-50" onclick="use5050()">⚡ 50:50</button>
                    <button class="life-btn" id="btn-class" onclick="askClass()">👥 Hỏi Ý Kiến Lớp</button>
                </div>
            </div>
            <script>
                const questions = QUIZ_PLACEHOLDER;
                let currentIdx = 0;

                function loadQuestion() {
                    if(currentIdx >= questions.length) {
                        document.getElementById('game-box').innerHTML = "<h2 style='color:#00e676;'>🎉 XUẤT SẮC VƯỢT QUA TẤT CẢ CÂU HỎI!</h2><p>Học sinh đã chiến thắng mốc phần thưởng cao nhất!</p>";
                        confetti({particleCount: 200, spread: 100});
                        return;
                    }
                    document.getElementById('score-board').innerText = "CÂU HỎI SỐ: " + (currentIdx + 1) + " / " + questions.length;
                    const qData = questions[currentIdx];
                    document.getElementById('question-text').innerText = qData.cau_hoi;
                    
                    const optionsBox = document.getElementById('options-box');
                    optionsBox.innerHTML = "";
                    
                    qData.options.forEach((opt, i) => {
                        const btn = document.createElement('button');
                        btn.className = 'opt-btn';
                        btn.innerHTML = "<b>" + String.fromCharCode(65 + i) + ":</b> " + opt;
                        btn.onclick = () => checkAnswer(opt, btn);
                        optionsBox.appendChild(btn);
                    });
                }

                function checkAnswer(selectedOpt, btn) {
                    const correctAns = questions[currentIdx].dap_an;
                    if(selectedOpt === correctAns) {
                        btn.style.background = "#00e676";
                        btn.style.color = "black";
                        setTimeout(() => {
                            currentIdx++;
                            loadQuestion();
                        }, 1500);
                    } else {
                        btn.style.background = "#ff4b4b";
                        alert("❌ Câu trả lời chưa chính xác! Hãy khuyến khích học sinh khác cứu trợ.");
                    }
                }

                function use5050() {
                    document.getElementById('btn-50').classList.add('used');
                    const correctAns = questions[currentIdx].dap_an;
                    const buttons = document.getElementsByClassName('opt-btn');
                    let removed = 0;
                    for(let btn of buttons) {
                        if(!btn.innerText.includes(correctAns) && removed < 2) {
                            btn.style.visibility = 'hidden';
                            removed++;
                        }
                    }
                }

                function askClass() {
                    document.getElementById('btn-class').classList.add('used');
                    alert("📊 Thầy/Cô hãy lấy biểu quyết nhanh từ các tổ trong lớp học!");
                }
                loadQuestion();
            </script>
        </body>
        </html>
        """.replace("QUIZ_PLACEHOLDER", js_quiz)
        
        components.html(millionaire_html, height=480)

# --- TAB 4: KỊCH BẢN SƯ PHẠM ---
with tabs[3]:
    st.header("📋 Khung Kịch Bản Bài Giảng Sư Phạm Cao Cấp")
    framework_type = st.selectbox("Chọn mô hình thiết kế", ["Mô hình 5E (Engage - Explore - Explain - Elaborate - Evaluate)", "Phương pháp giáo dục STEM/STEAM Integration", "Phát triển năng lực số"])
    if st.button("🛠 Sinh kịch bản sư phạm tổng thể"):
        if not st.session_state.current_topic:
            st.warning("Vui lòng qua Tab 'Thiết Kế Câu Hỏi AI' để tạo chủ đề bài học trước.")
        else:
            with st.spinner("AI đang biên soạn kịch bản chi tiết..."):
                script_prompt = f"Viết kịch bản dạy học chuẩn sư phạm cho bài học {st.session_state.current_topic} dựa trên {framework_type} cho học sinh {grade}."
                script_res = ai_engine.generate_content(script_prompt)
                st.markdown(script_res)

# --- TAB 5: XUẤT BẢN TÀI LIỆU ---
with tabs[4]:
    st.header("💾 Xuất Bản Học Liệu Số")
    if st.session_state.generated_quiz:
        st.write(f"Học liệu hiện hành sẵn có cho bài học: **{st.session_state.current_topic}**")
        
        c_down1, c_down2 = st.columns(2)
        with c_down1:
            docx_file = DocumentExporter.export_to_docx(st.session_state.current_topic, st.session_state.generated_quiz)
            st.download_button(
                label="📥 Tải xuống Giáo án Word (.docx)",
                data=docx_file,
                file_name=f"Giao_an_AI_{st.session_state.current_topic}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        with c_down2:
            pptx_file = DocumentExporter.export_to_pptx(st.session_state.current_topic, st.session_state.generated_quiz)
            st.download_button(
                label="📥 Tải xuống Slide Trình Chiếu (.pptx)",
                data=pptx_file,
                file_name=f"Slide_Game_{st.session_state.current_topic}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
    else:
        st.info("Chưa có dữ liệu học liệu được tạo từ AI. Hãy hoàn tất tạo câu hỏi ở Tab 2 để tiến hành xuất file.")
