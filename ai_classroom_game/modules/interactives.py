import streamlit as st
import streamlit.components.v1 as components
import json

def render_lucky_wheel(names_list, questions_list):
    st.subheader("🎡 Vòng Quay May Mắn (Màn hình tương tác lớn)")
    
    # Ép kiểu mảng dữ liệu sang chuỗi JSON an toàn cho JS
    js_names = json.dumps(names_list, ensure_ascii=False)
    js_questions = json.dumps(questions_list, ensure_ascii=False)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="[https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js](https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js)"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background: #121214; color: white; margin:0; padding:10px; }}
            .container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 85vh; }}
            canvas {{ border: 4px solid #fff; border-radius: 50%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); background: #1e1e24; }}
            button {{ background: #ff4b4b; color: white; border: none; padding: 15px 40px; font-size: 20px; font-weight: bold; border-radius: 30px; cursor: pointer; margin-top: 20px; box-shadow: 0 5px 15px rgba(255,75,75,0.4); transition: 0.2s; }}
            button:hover {{ transform: scale(1.05); background: #ff3333; }}
            #pointer {{ width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 30px solid #ffff00; position: absolute; top: calc(50% - 210px); z-index: 10; }}
            #result {{ font-size: 28px; font-weight: bold; margin-top: 20px; color: #00e676; text-shadow: 0 2px 4px rgba(0,0,0,0.5); min-height: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="pointer"></div>
            <canvas id="wheel" width="400" height="400"></canvas>
            <button onclick="spin()">VÒNG QUAY BẮT ĐẦU</button>
            <div id="result"></div>
        </div>

        <script>
            const names = {js_names};
            const questions = {js_questions};
            const canvas = document.getElementById('wheel');
            const ctx = canvas.getContext('2d');
            const numSegments = names.length || 1;
            const anglePerSegment = (2 * Math.PI) / numSegments;
            let currentAngle = 0;
            let isSpinning = false;

            function drawWheel() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const colors = ['#FF5722', '#E91E63', '#9C27B0', '#3F51B5', '#00BCD4', '#4CAF50', '#FFEB3B', '#FF9800'];
                
                for (let i = 0; i < numSegments; i++) {{
                    const startAngle = i * anglePerSegment + currentAngle;
                    const endAngle = startAngle + anglePerSegment;
                    
                    ctx.beginPath();
                    ctx.moveTo(200, 200);
                    ctx.arc(200, 200, 190, startAngle, endAngle);
                    ctx.fillStyle = colors[i % colors.length];
                    ctx.fill();
                    ctx.stroke();
                    
                    // Vẽ text nhãn học sinh
                    ctx.save();
                    ctx.translate(200, 200);
                    ctx.rotate(startAngle + anglePerSegment / 2);
                    ctx.fillStyle = "#fff";
                    ctx.font = "bold 14px sans-serif";
                    ctx.textAlign = "right";
                    ctx.fillText(names[i] || "Trống", 170, 5);
                    ctx.restore();
                }}
            }}

            function spin() {{
                if (isSpinning) return;
                isSpinning = true;
                document.getElementById('result').innerText = "Đang chọn nhân tài...";
                
                const spinAngles = 10 * 360 + Math.random() * 360;
                const duration = 4000; 
                const startTime = performance.now();

                function animate(currentTime) {{
                    const elapsed = currentTime - startTime;
                    if (elapsed >= duration) {{
                        isSpinning = false;
                        // Xác định mục tiêu trúng giải tại mốc 12 giờ (tức góc -Math.PI/2)
                        const normalizedAngle = (currentAngle % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
                        const winningIndex = Math.floor((2 * Math.PI - normalizedAngle - Math.PI/2) / anglePerSegment) % numSegments;
                        const finalIdx = winningIndex < 0 ? winningIndex + numSegments : winningIndex;
                        
                        const selectedPerson = names[finalIdx] || "Học sinh may mắn";
                        const selectedQuestion = questions[finalIdx % questions.length] || "Trả lời câu hỏi bất kỳ từ giáo viên!";
                        
                        document.getElementById('result').innerHTML = "🎯 " + selectedPerson + "<br><span style='color:#fff; font-size:18px;'>CHỦ ĐỀ: " + selectedQuestion + "</span>";
                        
                        confetti({{ particleCount: 150, spread: 80, origin: {{ y: 0.6 }} }});
                        return;
                    }}
                    
                    const progress = elapsed / duration;
                    const easeOutQuad = 1 - (1 - progress) * (1 - progress); 
                    currentAngle = (spinAngles * easeOutQuad * Math.PI) / 180;
                    drawWheel();
                    requestAnimationFrame(animate);
                }}
                requestAnimationFrame(animate);
            }}
            drawWheel();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=550, scrolling=False)
