import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from shapely.geometry import Point, Line, Polygon
import io

class GeometryEngine:
    @staticmethod
    def execute_drawing_code(code_str: str, config: dict) -> plt.Figure:
        """
        Thực thi đoạn mã vẽ do AI sinh ra và áp dụng cấu hình local (màu sắc, độ dày nét,...)
        """
        # Chuẩn bị môi trường thực thi với các thư viện cần thiết
        local_vars = {
            'plt': plt,
            'np': np,
            'sp': sp,
            'Point': Point,
            'Line': Line,
            'Polygon': Polygon
        }
        
        # Tạo sẵn fig và ax để code chèn vào
        fig, ax = plt.subplots(figsize=(8, 6))
        local_vars['fig'] = fig
        local_vars['ax'] = ax
        
        # Thực thi code
        # Lưu ý an toàn: Trong thực tế cần sanitize hoặc dùng sandbox. Ở đây exec phục vụ việc sinh code linh hoạt.
        exec(code_str, globals(), local_vars)
        
        # Áp dụng các tùy chỉnh từ UI lên các nét vẽ nếu có
        ax = local_vars['ax']
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
