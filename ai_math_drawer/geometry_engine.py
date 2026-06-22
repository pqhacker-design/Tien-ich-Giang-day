import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
import io

# Import an toàn cho mọi phiên bản Shapely
try:
    from shapely import Point, LineString, Polygon
    # Tạo nghệ danh (alias) Line tương đương LineString để chiều theo cách viết của AI
    Line = LineString 
except ImportError:
    from shapely.geometry import Point, Line, Polygon
    LineString = Line

class GeometryEngine:
    @staticmethod
    def execute_drawing_code(code_str: str, config: dict) -> plt.Figure:
        """
        Thực thi đoạn mã vẽ do AI sinh ra và áp dụng cấu hình local (màu sắc, độ dày nét,...)
        """
        # Chuẩn bị môi trường thực thi và nạp đầy đủ các biến mà AI có thể gọi
        local_vars = {
            'plt': plt,
            'np': np,
            'sp': sp,
            'Point': Point,
            'Line': Line,            # Định nghĩa Line để sửa lỗi "name 'Line' is not defined"
            'LineString': LineString,  # Dự phòng nếu AI dùng LineString
            'Polygon': Polygon
        }
        
        # Tạo sẵn fig và ax để code của AI chèn vào
        fig, ax = plt.subplots(figsize=(8, 6))
        local_vars['fig'] = fig
        local_vars['ax'] = ax
        
        # Thực thi mã nguồn do AI sinh ra trong môi trường đã nạp đủ thư viện
        exec(code_str, globals(), local_vars)
        
        # Lấy ax sau khi AI đã vẽ xong để tùy chỉnh giao diện theo UI gán vào từ Sidebar
        ax = local_vars['ax']
        
        # Áp dụng các tùy chỉnh từ UI lên các nét vẽ (nếu có)
        for line in ax.get_lines():
            if config.get('line_color'):
                line.set_color(config['line_color'])
            if config.get('line_width'):
                line.set_linewidth(config['line_width'])
                
        for text in ax.get_texts():
            if config.get('font_size'):
                text.set_fontsize(config['font_size'])
                
        return local_vars['fig']

    @staticmethod
    def convert_fig_to_image(fig: plt.Figure, dpi: int = 300, format: str = 'png') -> io.BytesIO:
        """Chuyển đổi Figure Matplotlib thành bộ nhớ BytesIO để tải về hoặc chèn vào Word"""
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return buf
