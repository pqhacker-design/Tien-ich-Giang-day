import streamlit as st
import streamlit.components.v1 as components
import json
import os

# Cấu hình trang hiển thị của Streamlit
st.set_page_config(
    page_title="Classroom Lucky Wheel & Student Picker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "students_data.json"

# --- HÀM XỬ LÝ DỮ LIỆU FILE (BACKEND PYTHON) ---
def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "classes": {
            "6A1": [
                {"id": "1", "name": "Nguyễn An", "class": "6A1", "gender": "Nam", "avatar": "", "score": 0},
                {"id": "2", "name": "Trần Thị Bình", "class": "6A1", "gender": "Nữ", "avatar": "", "score": 0},
                {"id": "3", "name": "Lê Minh Cường", "class": "6A1", "gender": "Nam", "avatar": "", "score": 0}
            ]
        },
        "currentClass": "6A1"
    }

def save_database(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# Khởi tạo Session State trong Streamlit
if "db" not in st.session_state:
    st.session_state.db = load_database()

db = st.session_state.db

# --- GIAO DIỆN QUẢN LÝ DỮ LIỆU TRÊN SIDEBAR STREAMLIT ---
st.sidebar.title("⚙️ Cấu Hình Lớp Học")

class_list = list(db["classes"].keys())
if not class_list:
    class_list = ["6A1"]
    db["classes"]["6A1"] = []

current_class = st.sidebar.selectbox("Chọn lớp giảng dạy:", class_list, index=class_list.index(db["currentClass"]) if db["currentClass"] in class_list else 0)
db["currentClass"] = current_class

# 1. Thêm lớp mới nhanh
new_class_input = st.sidebar.text_input("➕ Tạo lớp học mới:")
if st.sidebar.button("Tạo lớp") and new_class_input.strip():
    c_name = new_class_input.strip()
    if c_name not in db["classes"]:
        db["classes"][c_name] = []
        db["currentClass"] = c_name
        save_database(db)
        st.rerun()

st.sidebar.write("---")

# 2. TÍNH NĂNG MỚI: NHẬP DÀNH SÁCH HÀNG LOẠT TỪ EXCEL
st.sidebar.subheader("📥 Nhập danh sách từ Excel")
st.sidebar.caption("Thầy quét khối cột 'Họ và tên' trong Excel, bấm Ctrl+C rồi dán vào ô dưới đây:")

excel_paste = st.sidebar.text_area("Dán danh sách học sinh vào đây (mỗi tên 1 dòng):", height=150, key="excel_input")

col_ex1, col_ex2 = st.sidebar.columns(2)
with col_ex1:
    if st.button("➕ Thêm nối tiếp", help="Giữ lại danh sách cũ, thêm tên mới vào cuối"):
        if excel_paste.strip():
            lines = [line.strip() for line in excel_paste.split("\n") if line.strip()]
            start_id = len(db["classes"][current_class]) + 101
            for idx, name in enumerate(lines):
                db["classes"][current_class].append({
                    "id": str(start_id + idx),
                    "name": name,
                    "class": current_class,
                    "gender": "Nam",
                    "avatar": "",
                    "score": 0
                })
            save_database(db)
            st.sidebar.success(f"Đã thêm thêm {len(lines)} học sinh!")
            st.rerun()

with col_ex2:
    if st.button("🔄 Ghi đè lớp", help="Xóa sạch danh sách hiện tại của lớp này và thay bằng danh sách mới"):
        if excel_paste.strip():
            lines = [line.strip() for line in excel_paste.split("\n") if line.strip()]
            db["classes"][current_class] = [] # Xóa sạch lớp hiện tại
            for idx, name in enumerate(lines):
                db["classes"][current_class].append({
                    "id": str(101 + idx),
                    "name": name,
                    "class": current_class,
                    "gender": "Nam",
                    "avatar": "",
                    "score": 0
                })
            save_database(db)
            st.sidebar.success(f"Đã làm mới lớp với {len(lines)} học sinh!")
            st.rerun()

# --- ĐỒNG BỘ DỮ LIỆU SANG WEB COMPONENT ---
db_json_string = json.dumps(db, ensure_ascii=False)

# --- CODE GIAO DIỆN HOÀN CHỈNH (HTML/CSS/JS) ---
frontend_html = f"""
<!DOCTYPE html>
<html lang="vi" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <style>
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .animate-fadeIn {{ animation: fadeIn 0.35s ease forwards; }}
        .tab-btn {{ color: #64748b; background-color: transparent; }}
        html[data-theme="dark"] .tab-btn {{ color: #94a3b8; }}
        .tab-btn.active {{ background-color: #4f46e5; color: #ffffff !important; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3); }}
        
        .wheel-container {{ 
            position: relative; 
            width: 380px; 
            height: 380px; 
            max-width: 100%; 
            aspect-ratio: 1/1;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .wheel-pointer {{ 
            position: absolute; 
            top: -12px; 
            left: 50%; 
            transform: translateX(-50%); 
            width: 0; 
            height: 0; 
            border-left: 16px solid transparent; 
            border-right: 16px solid transparent; 
            border-top: 28px solid #f43f5e; 
            z-index: 50; 
            filter: drop-shadow(0px 3px 4px rgba(0,0,0,0.15)); 
        }}
        #wheelCanvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
        
        .card-flip {{ perspective: 1000px; cursor: pointer; }}
        .card-inner {{ position: relative; width: 100%; height: 130px; text-align: center; transition: transform 0.5s; transform-style: preserve-3d; }}
        .card-flip.flipped .card-inner {{ transform: rotateY(180deg); }}
        .card-front, .card-back {{ position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; border-radius: 1rem; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem; }}
        .card-front {{ background: linear-gradient(135deg, #6366f1, #a855f7); color: white; }}
        .card-back {{ background-color: white; transform: rotateY(180deg); }}
        html[data-theme="dark"] .card-back {{ background-color: #1e293b; }}
        .group-drop-zone {{ min-height: 110px; }}
        .group-drop-zone.drag-over {{ background-color: rgba(79, 70, 229, 0.1); border-color: #4f46e5 !important; }}
    </style>
</head>
<body class="bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen transition-colors duration-200">

    <header class="bg-white dark:bg-slate-800 shadow-sm px-4 py-3 flex justify-between items-center">
        <div class="flex items-center space-x-3">
            <div class="bg-indigo-600 text-white p-2 rounded-lg shadow-md"><i class="fas fa-dharmachakra text-lg"></i></div>
            <div>
                <h1 class="text-lg font-bold bg-gradient-to-r from-indigo-600 to-pink-500 bg-clip-text text-transparent">Classroom Lucky Wheel</h1>
                <p class="text-[11px] text-slate-400">Đồng bộ đám mây Streamlit Hub</p>
            </div>
        </div>
        <div class="flex items-center space-x-2">
            <span class="bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 px-3 py-1.5 rounded-xl font-bold text-xs"><i class="fas fa-school mr-1"></i> Lớp đang chọn: {current_class}</span>
            <button id="btnToggleTheme" class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-base"><i class="fas fa-moon dark:hidden"></i><i class="fas fa-sun hidden dark:inline text-amber-400"></i></button>
        </div>
    </header>

    <nav class="bg-indigo-50/50 dark:bg-slate-800/30 p-2 overflow-x-auto whitespace-nowrap border-b border-slate-200 dark:border-slate-700 flex justify-start md:justify-center space-x-1.5">
        <button onclick="switchTab('tab-wheel')" class="tab-btn active px-4 py-2 rounded-full text-xs font-bold transition-all"><i class="fas fa-dharmachakra mr-1"></i>Vòng Quay</button>
        <button onclick="switchTab('tab-grid')" class="tab-btn px-4 py-2 rounded-full text-xs font-bold transition-all"><i class="fas fa-th-large mr-1"></i>Lưới Thẻ Bí Mật</button>
        <button onclick="switchTab('tab-random')" class="tab-btn px-4 py-2 rounded-full text-xs font-bold transition-all"><i class="fas fa-random mr-1"></i>Gọi Tên Siêu Tốc</button>
        <button onclick="switchTab('tab-group')" class="tab-btn px-4 py-2 rounded-full text-xs font-bold transition-all"><i class="fas fa-layer-group mr-1"></i>Chia Nhóm</button>
        <button onclick="switchTab('tab-leaderboard')" class="tab-btn px-4 py-2 rounded-full text-xs font-bold transition-all"><i class="fas fa-trophy mr-1"></i>Bảng Điểm</button>
    </nav>

    <main class="max-w-7xl mx-auto p-4">
        <section id="tab-wheel" class="tab-content block animate-fadeIn">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
                <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 space-y-4">
                    <h3 class="text-sm font-bold text-indigo-600"><i class="fas fa-sliders-h mr-1"></i>Cấu Hình Lượt Quay</h3>
                    <div class="space-y-2 text-xs">
                        <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="wheelMode" value="keep" checked><span>Giữ lại học sinh sau khi trúng</span></label>
                        <label class="flex items-center space-x-2 cursor-pointer text-red-500"><input type="radio" name="wheelMode" value="remove"><span>Loại bỏ khỏi lượt sau</span></label>
                    </div>
                    <div id="wheelAttendanceStatus" class="text-xs text-slate-400 pt-2 border-t"></div>
                </div>
                <div class="lg:col-span-2 flex flex-col items-center justify-center relative py-6">
                    <div class="wheel-container shadow-2xl rounded-full border-4 border-white dark:border-slate-800 relative">
                        <div class="wheel-pointer"></div>
                        <canvas id="wheelCanvas" width="500" height="500"></canvas>
                    </div>
                    <button id="btnSpin" class="mt-8 bg-gradient-to-r from-pink-500 to-rose-500 text-white font-black text-base px-12 py-3.5 rounded-full shadow-lg hover:scale-105 transition transform active:scale-95"><i class="fas fa-play mr-1"></i>BẮT ĐẦU QUAY</button>
                </div>
            </div>
        </section>

        <section id="tab-grid" class="tab-content hidden animate-fadeIn">
            <div class="flex justify-between items-center mb-4">
                <label class="flex items-center space-x-2 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl text-xs border cursor-pointer"><input type="checkbox" id="chkSecretMode" checked><span class="font-bold text-amber-500">Chế độ Lật Thẻ Ẩn Danh</span></label>
                <button id="btnResetGrid" class="text-xs font-bold bg-indigo-50 text-indigo-600 dark:bg-slate-800 px-3 py-1.5 rounded-lg">Khôi phục lưới</button>
            </div>
            <div id="interactiveGrid" class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4"></div>
        </section>

        <section id="tab-random" class="tab-content hidden animate-fadeIn">
            <div class="max-w-xl mx-auto text-center py-8 space-y-6">
                <div class="bg-white dark:bg-slate-800 h-48 rounded-3xl shadow-md border-2 border-dashed border-indigo-200 flex flex-col items-center justify-center p-4">
                    <div id="randomDisplayName" class="text-3xl md:text-5xl font-black text-indigo-600">SẴN SÀNG</div>
                </div>
                <button id="btnTriggerRandom" class="bg-indigo-600 text-white font-extrabold text-base px-10 py-3.5 rounded-xl shadow-md">GỌI TÊN NGẪU NHIÊN</button>
            </div>
        </section>

        <section id="tab-group" class="tab-content hidden animate-fadeIn">
            <div class="bg-white dark:bg-slate-800 p-4 rounded-xl border mb-4 text-xs flex flex-wrap gap-4 items-end">
                <div><label class="block mb-1 font-bold">Tiêu chí</label><select id="groupRule" class="bg-slate-50 dark:bg-slate-700 p-2 rounded-lg outline-none"><option value="numGroups">Chia thành số nhóm</option><option value="sizeGroup">Số HS mỗi nhóm</option></select></div>
                <div><label class="block mb-1 font-bold">Số lượng</label><input type="number" id="groupValue" value="3" class="bg-slate-50 dark:bg-slate-700 p-2 rounded-lg w-20"></div>
                <button id="btnGenerateGroups" class="bg-indigo-600 text-white font-bold px-4 py-2 rounded-lg">Thực hiện chia</button>
            </div>
            <div id="groupsContainer" class="grid grid-cols-1 md:grid-cols-3 gap-4"></div>
        </section>

        <section id="tab-leaderboard" class="tab-content hidden animate-fadeIn">
            <div class="bg-white dark:bg-slate-800 rounded-xl border max-w-2xl mx-auto overflow-hidden">
                <table class="w-full text-xs text-left">
                    <thead class="bg-slate-50 dark:bg-slate-700 font-bold"><tr><th class="p-3 w-16 text-center">Hạng</th><th class="p-3">Học sinh</th><th class="p-3 text-center">Điểm số</th><th class="p-3 text-center">Tương tác</th></tr></thead>
                    <tbody id="leaderboardTableBody" class="divide-y"></tbody>
                </table>
            </div>
        </section>
    </main>

    <div id="winnerModal" class="fixed inset-0 bg-black/60 backdrop-blur-xs z-[100] flex items-center justify-center opacity-0 pointer-events-none transition-opacity duration-200">
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-xs w-full text-center transform scale-95 transition-transform duration-200 shadow-xl">
            <h4 class="text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">Chúc mừng học sinh</h4>
            <h2 id="winnerName" class="text-2xl font-black text-indigo-600 my-3">Nguyễn Văn A</h2>
            <div class="flex gap-2"><button onclick="modifyWinnerScore(10)" class="flex-1 bg-amber-500 text-white text-xs font-bold py-2 rounded-xl">+10 Điểm</button><button onclick="closeWinnerModal()" class="flex-1 bg-slate-100 dark:bg-slate-700 text-xs py-2 rounded-xl">Đóng</button></div>
        </div>
    </div>

    <script>
        let database = {db_json_string};
        let currentClassName = "{current_class}";
        let excludedStudentIds = new Set();
        let audioCtx = null;
        let wheelAngle = 0;
        let isWheelSpinning = false;
        const colors = ["#4f46e5", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6", "#ef4444", "#06b6d4"];

        function getCurrentStudents() {{
            return database.classes[currentClassName] || [];
        }}

        function switchTab(tabId) {{
            document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
            document.getElementById(tabId).classList.remove("hidden");
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
            const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(btn => btn.getAttribute("onclick").includes(tabId));
            if (activeBtn) activeBtn.classList.add("active");
            if (tabId === 'tab-wheel') initWheelCanvas();
            if (tabId === 'tab-grid') renderInteractiveGrid();
            if (tabId === 'tab-leaderboard') renderLeaderboard();
        }}

        function playSound(type) {{
            try {{
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain); gain.connect(audioCtx.destination);
                if (type === 'tick') {{
                    osc.frequency.setValueAtTime(550, audioCtx.currentTime);
                    gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.04);
                    osc.start(); osc.stop(audioCtx.currentTime + 0.05);
                }} else if (type === 'win') {{
                    osc.type = 'triangle'; osc.frequency.setValueAtTime(440, audioCtx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.25);
                    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                    osc.start(); osc.stop(audioCtx.currentTime + 0.3);
                }}
            }} catch(e) {{}}
        }}

        function speakVietnamese(text) {{
            if ('speechSynthesis' in window) {{
                const utter = new SpeechSynthesisUtterance(text);
                utter.lang = 'vi-VN';
                window.speechSynthesis.speak(utter);
            }}
        }}

        function initWheelCanvas() {{
            const canvas = document.getElementById("wheelCanvas");
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            const students = getCurrentStudents().filter(s => !excludedStudentIds.has(s.id));
            document.getElementById("wheelAttendanceStatus").innerText = `Đang tham gia: ${{students.length}} HS. Loại trừ: ${{excludedStudentIds.size}}.`;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const center = canvas.width / 2;
            
            if (students.length === 0) {{
                ctx.fillStyle = "#94a3b8"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center";
                ctx.fillText("Vòng quay trống", center, center); return;
            }}
            
            const arcSize = (Math.PI * 2) / students.length;
            students.forEach((s, i) => {{
                const startAngle = wheelAngle + (i * arcSize);
                const endAngle = startAngle + arcSize;
                
                ctx.beginPath(); 
                ctx.fillStyle = colors[i % colors.length]; 
                ctx.moveTo(center, center);
                ctx.arc(center, center, center - 12, startAngle, endAngle); 
                ctx.fill();
                
                ctx.lineWidth = 2; 
                ctx.strokeStyle = "#ffffff"; 
                ctx.stroke();
                
                ctx.save(); 
                ctx.fillStyle = "#ffffff"; 
                ctx.textAlign = "right"; 
                ctx.font = "bold 15px sans-serif";
                ctx.translate(center, center); 
                ctx.rotate(startAngle + arcSize / 2);
                ctx.fillText(s.name, center - 35, 5); 
                ctx.restore();
            }});
            
            ctx.beginPath(); 
            ctx.fillStyle = "#ffffff"; 
            ctx.arc(center, center, 24, 0, Math.PI * 2); 
            ctx.fill();
            ctx.strokeStyle = "#4f46e5"; 
            ctx.lineWidth = 4; 
            ctx.stroke();
        }}

        document.getElementById("btnSpin").addEventListener("click", () => {{
            if (isWheelSpinning) return;
            const students = getCurrentStudents().filter(s => !excludedStudentIds.has(s.id));
            if (students.length === 0) return;
            isWheelSpinning = true;
            let duration = 3500; let startTimestamp = null;
            const targetSpinAngle = (Math.PI * 2 * 7) + Math.random() * (Math.PI * 2);
            let lastTickAngle = 0;
            function animateWheel(timestamp) {{
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = timestamp - startTimestamp;
                const ratio = Math.min(progress / duration, 1);
                const easeOutQuad = 1 - Math.pow(1 - ratio, 3);
                wheelAngle = easeOutQuad * targetSpinAngle;
                if (wheelAngle - lastTickAngle > 0.2) {{ playSound('tick'); lastTickAngle = wheelAngle; }}
                initWheelCanvas();
                if (ratio < 1) {{ requestAnimationFrame(animateWheel); }} else {{
                    isWheelSpinning = false;
                    const arcSize = (Math.PI * 2) / students.length;
                    const normalizedAngle = (Math.PI * 2 - (wheelAngle % (Math.PI * 2))) % (Math.PI * 2);
                    
                    let correctedAngle = normalizedAngle - (Math.PI / 2);
                    if (correctedAngle >= Math.PI * 2) correctedAngle -= Math.PI * 2;
                    
                    const winningIndex = Math.floor(correctedAngle / arcSize);
                    triggerWinner(students[winningIndex]);
                }}
            }}
            requestAnimationFrame(animateWheel);
        }});

        function triggerWinner(student) {{
            if(!student) return;
            confetti({{ particleCount: 100, spread: 60, origin: {{ y: 0.7 }} }});
            document.getElementById("winnerName").innerText = student.name;
            const modal = document.getElementById("winnerModal");
            modal.classList.remove("pointer-events-none", "opacity-0");
            modal.children[0].classList.remove("scale-95");
            playSound('win');
            setTimeout(() => {{ speakVietnamese(student.name); }}, 300);
            if (document.querySelector('input[name="wheelMode"]:checked').value === 'remove') {{
                excludedStudentIds.add(student.id);
            }}
        }}

        window.closeWinnerModal = function() {{
            const modal = document.getElementById("winnerModal");
            modal.classList.add("pointer-events-none", "opacity-0");
            modal.children[0].classList.add("scale-95");
            initWheelCanvas();
        }}

        window.modifyWinnerScore = function(points) {{
            const students = getCurrentStudents();
            const student = students.find(s => s.name === document.getElementById("winnerName").innerText);
            if(student) {{
                student.score = (student.score || 0) + points;
            }}
            closeWinnerModal();
        }}

        function renderInteractiveGrid() {{
            const students = getCurrentStudents();
            const grid = document.getElementById("interactiveGrid");
            grid.innerHTML = "";
            const isSecret = document.getElementById("chkSecretMode").checked;
            students.forEach(s => {{
                const div = document.createElement("div");
                div.className = `card-flip ${{isSecret ? '' : 'flipped'}}`;
                div.innerHTML = `
                    <div class="card-inner">
                        <div class="card-front"><i class="fas fa-question text-xl opacity-60"></i></div>
                        <div class="card-back border text-center p-2 flex flex-col justify-center items-center rounded-xl">
                            <span class="text-xs font-bold truncate max-w-full">${{s.name}}</span>
                            <span class="text-[10px] text-indigo-500 font-bold mt-1">★ ${{s.score}}</span>
                        </div>
                    </div>
                `;
                div.addEventListener("click", () => {{
                    if (isSecret && !div.classList.contains("flipped")) {{
                        div.classList.add("flipped"); playSound('tick');
                    }} else {{ triggerWinner(s); }}
                }});
                grid.appendChild(div);
            }});
        }}
        document.getElementById("chkSecretMode").addEventListener("change", renderInteractiveGrid);
        document.getElementById("btnResetGrid").addEventListener("click", renderInteractiveGrid);

        document.getElementById("btnTriggerRandom").addEventListener("click", () => {{
            const students = getCurrentStudents(); if (students.length === 0) return;
            let count = 0;
            let interval = setInterval(() => {{
                const r = students[Math.floor(Math.random() * students.length)];
                document.getElementById("randomDisplayName").innerText = r.name.toUpperCase();
                playSound('tick'); count++;
                if (count > 12) {{
                    clearInterval(interval);
                    const final = students[Math.floor(Math.random() * students.length)];
                    document.getElementById("randomDisplayName").innerText = final.name.toUpperCase();
                    triggerWinner(final);
                }}
            }}, 100);
        }});

        document.getElementById("btnGenerateGroups").addEventListener("click", () => {{
            const students = [...getCurrentStudents()]; if (students.length === 0) return;
            for (let i = students.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1)); [students[i], students[j]] = [students[j], students[i]];
            }}
            const rule = document.getElementById("groupRule").value;
            const val = parseInt(document.getElementById("groupValue").value) || 2;
            let numG = rule === 'numGroups' ? val : Math.ceil(students.length / val);
            const container = document.getElementById("groupsContainer"); container.innerHTML = "";
            
            for(let g=0; g<numG; g++) {{
                const gBox = document.createElement("div");
                gBox.className = "bg-white dark:bg-slate-800 border p-3 rounded-xl";
                gBox.innerHTML = `<h4 class="font-bold text-xs text-indigo-600 mb-2">Nhóm ${{g+1}}</h4><div class="group-drop-zone space-y-1" data-g="${{g}}"></div>`;
                container.appendChild(gBox);
            }}
            students.forEach((s, idx) => {{
                const targetZone = container.querySelectorAll(".group-drop-zone")[idx % numG];
                const item = document.createElement("div");
                item.className = "bg-slate-50 dark:bg-slate-700 p-1.5 text-[11px] font-medium rounded-lg";
                item.innerText = s.name; targetZone.appendChild(item);
            }});
        }});

        function renderLeaderboard() {{
            const students = [...getCurrentStudents()].sort((a,b) => b.score - a.score);
            const tbody = document.getElementById("leaderboardTableBody"); tbody.innerHTML = "";
            students.forEach((s, i) => {{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td class="p-3 text-center font-bold">${{i+1}}</td>
                    <td class="p-3 font-bold">${{s.name}}</td>
                    <td class="p-3 text-center text-indigo-600 font-bold">${{s.score}}đ</td>
                    <td class="p-3 text-center"><button onclick="addScoreDirect('${{s.id}}', 5)" class="bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded font-bold text-[10px]">+5đ</button></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        window.addScoreDirect = function(id, val) {{
            const s = getCurrentStudents().find(x => x.id === id);
            if(s) {{ s.score = (s.score || 0) + val; renderLeaderboard(); }}
        }}

        document.getElementById("btnToggleTheme").addEventListener("click", () => {{
            const t = document.documentElement.getAttribute("data-theme") === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute("data-theme", t);
            if(t==='dark') document.documentElement.classList.add("dark"); else document.documentElement.classList.remove("dark");
            initWheelCanvas();
        }});

        setTimeout(initWheelCanvas, 350);
    </script>
</body>
</html>
"""

# --- NHÚNG GIAO DIỆN VÀO ỨNG DỤNG STREAMLIT HUB ---
components.html(frontend_html, height=780, scrolling=False)

# --- PANEL QUẢN LÝ THÀNH VIÊN PYTHON (NẰM DƯỚI ỨNG DỤNG) ---
st.write("---")
st.subheader(f"📊 Bảng Chỉnh Sửa Học Sinh Lớp {current_class} (Admin Backend)")

students_list = db["classes"][current_class]

# Giao diện thêm nhanh học sinh bằng Python Streamlit
with st.form("Add Student Form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Họ tên học sinh:")
    with col2:
        new_gender = st.selectbox("Giới tính:", ["Nam", "Nữ"])
    
    if st.form_submit_button("🔥 Xác Nhận Thêm Vào Lớp") and new_name.strip():
        students_list.append({
            "id": str(len(students_list) + 101),
            "name": new_name.strip(),
            "class": current_class,
            "gender": new_gender,
            "avatar": "",
            "score": 0
        })
        save_database(db)
        st.success(f"Đã thêm thành công học sinh {new_name}!")
        st.rerun()

# Hiển thị và xóa học sinh
if students_list:
    for idx, s in enumerate(students_list):
        c_item1, c_item2, c_item3 = st.columns([3, 2, 1])
        c_item1.write(f"**{s['name']}**")
        c_item2.write(f"Điểm tích lũy: `{s['score']}đ`")
        if c_item3.button("🗑️ Xóa", key=f"del_{s['id']}_{idx}"):
            students_list.pop(idx)
            save_database(db)
            st.rerun()
else:
    st.info("Lớp học trống. Hãy thêm học sinh ở form trên.")
