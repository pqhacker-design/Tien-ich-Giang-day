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
        Thực thi đoạn mã vẽ do AI sinh ra và áp dụng cấu hình local
        """
        # Xóa tất cả các hình vẽ cũ đang chạy ngầm trong bộ nhớ để tránh bị đè hình
        plt.close('all') 
        
        # Tạo sẵn fig và ax mặc định để AI dùng luôn
        fig, ax = plt.subplots(figsize=(8, 6))
        
        local_vars = {
            'plt': plt,
            'np': np,
            'sp': sp,
            'Point': Point,
            'Line': Line,            
            'LineString': LineString,  
            'Polygon': Polygon,
            'fig': fig,
            'ax': ax
        }
        
        # Thực thi mã nguồn do AI sinh ra
        exec(code_str, globals(), local_vars)
        
        # 🛠️ CẢI TIẾN: Lấy Figure hiện tại đang hoạt động (Đảm bảo lấy đúng hình AI vừa vẽ)
        active_fig = plt.gcf()
        active_ax = active_fig.gca()
        
        # Áp dụng các tùy chỉnh từ UI gán từ Sidebar lên active_ax
        for line in active_ax.get_lines():
            if config.get('line_color'):
                line.set_color(config['line_color'])
            if config.get('line_width'):
                line.set_linewidth(config['line_width'])
                
        for text in active_ax.texts:
            if config.get('font_size'):
                text.set_fontsize(config['font_size'])
                
        return active_fig

    @staticmethod
    def convert_fig_to_image(fig: plt.Figure, dpi: int = 300, format: str = 'png') -> io.BytesIO:
        """Chuyển đổi Figure Matplotlib thành bộ nhớ BytesIO để tải về hoặc chèn vào Word"""
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return buf
