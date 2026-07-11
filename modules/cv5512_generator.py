def format_html_preview(lesson_json):
    """Chuyển đổi dữ liệu JSON từ AI thành định dạng HTML trực quan để preview trên giao diện"""
    if not isinstance(lesson_json, dict):
        return "<div class='error-box'>Dữ liệu không hợp lệ.</div>"

    if "error" in lesson_json:
        return f"<div class='error-box'>{lesson_json['error']}</div>"
        
    info = lesson_json.get("thong_tin_chung", {})
    muc_tieu = lesson_json.get("muc_tieu", {})
    
    # Lấy danh sách an toàn, hỗ trợ cả 2 cách đặt tên key
    pham_chat = muc_tieu.get("pham_chat", [])
    
    # Nếu AI trả về 'nang_luc' chung thay vì chia nhỏ
    nang_luc_chung = muc_tieu.get("nang_luc_chung", muc_tieu.get("nang_luc", []))
    nang_luc_dac_thu = muc_tieu.get("nang_luc_dac_thu", [])
    kien_thuc = muc_tieu.get("kien_thuc", [])

    html = f"""
    <div style='font-family: "Times New Roman", Times, serif; color: #111;'>
        <h2 style='text-align: center; color: #1E3A8A;'>KẾ HOẠCH BÀI DẠY (GIÁO ÁN 4.0)</h2>
        <p style='text-align: center;'><b>Môn:</b> {info.get('mon_hoc', '')} | <b>Khối:</b> {info.get('lop', '')} | <b>Thời lượng:</b> {info.get('thoi_luong', '')}</p>
        <h3 style='text-align: center; text-transform: uppercase;'>BÀI HỌC: {info.get('ten_bai_hoc', '')}</h3>
        <hr/>
        
        <h4>I. MỤC TIÊU BÀI HỌC</h4>
    """
    
    if kien_thuc:
        html += f"<h5>1. Kiến thức</h5><ul>{''.join([f'<li>{item}</li>' for item in kien_thuc])}</ul>"

    if nang_luc_chung:
        html += f"<h5>2. Năng lực</h5><ul>{''.join([f'<li>{item}</li>' for item in nang_luc_chung])}</ul>"
        
    if nang_luc_dac_thu:
        html += f"<h5>3. Năng lực đặc thù</h5><ul>{''.join([f'<li>{item}</li>' for item in nang_luc_dac_thu])}</ul>"

    if pham_chat:
        html += f"<h5>4. Phẩm chất chủ yếu</h5><ul>{''.join([f'<li>{item}</li>' for item in pham_chat])}</ul>"
        
    html += f"""
        <h4>II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU SỐ</h4>
        <ul>{"".join([f"<li>{item}</li>" for item in lesson_json.get('thiet_bi_day_hoc', [])])}</ul>
        
        <h4>III. TIẾN TRÌNH DẠY HỌC (CÔNG VĂN 5512)</h4>
    """
    
    for hd in lesson_json.get("tien_trinh_day_hoc", []):
        html += f"""
        <div style='margin-bottom: 15px; border-left: 3px solid #0284C7; padding-left: 10px;'>
            <b style='color: #0369A1;'>{hd.get('ten_hoat_dong', '')}</b><br/>
            <b>a) Mục tiêu:</b> {hd.get('muc_tieu', '')}<br/>
            <b>b) Nội dung:</b> {hd.get('noi_dung', '')}<br/>
            <b>c) Sản phẩm:</b> {hd.get('san_pham', '')}<br/>
            <b>d) Tổ chức thực hiện:</b> <p style='white-space: pre-wrap; margin: 2px 0;'>{hd.get('to_chuc_thuc_hien', '')}</p>
        </div>
        """
    html += "</div>"
    return html
