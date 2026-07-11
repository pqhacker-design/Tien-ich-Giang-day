import pandas as pd
from typing import List, Dict

class AIAnomalyDetector:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, mapping: Dict[str, str]) -> List[Dict[str, str]]:
        """Module 10: Phát hiện bất thường điểm số (Không tự sửa dữ liệu)"""
        anomalies = []
        name_col = mapping.get('name', '')
        gk_col = mapping.get('gk', '')
        ck_col = mapping.get('ck', '')
        
        if not name_col:
            return anomalies

        for idx, row in df.iterrows():
            name = row.get(name_col, f"Dòng {idx+1}")
            try:
                gk = float(row.get(gk_col, 0)) if pd.notnull(row.get(gk_col)) else None
                ck = float(row.get(ck_col, 0)) if pd.notnull(row.get(ck_col)) else None

                if gk is not None and (gk < 0 or gk > 10):
                    anomalies.append({"student": name, "issue": "Điểm Giữa kỳ ngoài thang điểm 0-10", "val": gk})
                if ck is not None and (ck < 0 or ck > 10):
                    anomalies.append({"student": name, "issue": "Điểm Cuối kỳ ngoài thang điểm 0-10", "val": ck})
                if gk is not None and ck is not None and abs(gk - ck) >= 4.0:
                    anomalies.append({"student": name, "issue": f"Điểm lệch bất thường giữa GK ({gk}) và CK ({ck})", "val": abs(gk-ck)})
            except ValueError:
                anomalies.append({"student": name, "issue": "Điểm số chứa ký tự sai định dạng", "val": "Error"})
                
        return anomalies
