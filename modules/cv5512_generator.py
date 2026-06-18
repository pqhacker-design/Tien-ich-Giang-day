def format_html_preview(lesson_json):
    """Chuyển đổi dữ liệu JSON từ AI thành định dạng HTML trực quan để preview trên giao diện"""
    if "error" in lesson_json:
        return f"<div class='error-box'>{lesson_json['error']}</div>"
        
    info = lesson_json.get("thong_tin_chung", {})
    html = f"""
    <div style='font-family: "Times New Roman", Times, serif; color: #111;'>
        <h2 style='text-align: center; color: #1E3A8A;'>KẾ HOẠCH BÀI DẠY (GIÁO ÁN 4.0)</h2>
        <p style='text-align: center;'><b>Môn:</b> {info.get('mon_hoc')} | <b>Khối:</b> {info.get('lop')} | <b>Thời lượng:</b> {info.get('thoi_luong')}</p>
        <h3 style='text-align: center; text-transform: uppercase;'>BÀI HỌC: {info.get('ten_bai_hoc')}</h3>
        <hr/>
        
        <h4>I. MỤC TIÊU BÀI HỌC</h4>
        <h5>1. Phẩm chất chủ yếu</h5>
        <ul>{"".join([f"<li>{item}</li>" for item in lesson_json['muc_tieu']['pham_chat']])}</ul>
        
        <h5>2. Năng lực chung</h5>
        <ul>{"".join([f"<li>{item}</li>" for item in lesson_json['muc_tieu']['nang_luc_chung']])}</ul>
        
        <h5>3. Năng lực đặc thù môn học</h5>
        <ul>{"".join([f"<li>{item}</li>" for item in lesson_json['muc_tieu']['nang_luc_dac_thu']])}</ul>
        
        <h4>II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU SỐ</h4>
        <ul>{"".join([f"<li>{item}</li>" for item in lesson_json.get('thiet_bi_day_hoc', [])])}</ul>
        
        <h4>III. TIẾN TRÌNH DẠY HỌC (CÔNG VĂN 5512)</h4>
    """
    
    for hd in lesson_json.get("tien_trinh_day_hoc", []):
        html += f"""
        <div style='margin-bottom: 15px; border-left: 3px solid #0284C7; padding-left: 10px;'>
            <b style='color: #0369A1;'>{hd.get('ten_hoat_dong')}</b><br/>
            <b>a) Mục tiêu:</b> {hd.get('muc_tieu')}<br/>
            <b>b) Nội dung:</b> {hd.get('noi_dung')}<br/>
            <b>c) Sản phẩm:</b> {hd.get('san_pham')}<br/>
            <b>d) Tổ chức thực hiện:</b> <p style='white-space: pre-wrap; margin: 2px 0;'>{hd.get('to_chuc_thuc_hien')}</p>
        </div>
        """
    html += "</div>"
    return html