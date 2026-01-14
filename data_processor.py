"""
Module xử lý dữ liệu mực nước
Data processor for water level analysis and alert generation
"""

import logging
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WaterLevelProcessor:
    """
    Class xử lý và phân tích dữ liệu mực nước
    """
    
    def __init__(self):
        """Khởi tạo processor"""
        self.timezone = pytz.timezone(config.TIMEZONE)
        self.stations = config.STATIONS
    
    def process_station_data(self, raw_data: Dict) -> Dict:
        """
        Xử lý dữ liệu thô từ scraper cho một trạm
        
        Args:
            raw_data: Dữ liệu thô từ scraper
            
        Returns:
            Dict chứa dữ liệu đã xử lý
        """
        station_id = raw_data.get('station_id')
        if not station_id or station_id not in self.stations:
            logger.error(f"✗ Station ID không hợp lệ: {station_id}")
            return {}
        
        station_info = self.stations[station_id]
        chart_data = raw_data.get('raw_data', {})
        data_points = chart_data.get('data', [])
        
        if not data_points:
            logger.warning(f"✗ Không có dữ liệu cho trạm {station_info['name']}")
            return {}
        
        # Chuyển đổi dữ liệu sang DataFrame
        df = self._convert_to_dataframe(data_points)
        
        if df.empty:
            return {}
        
        # Lấy thông tin hiện tại
        current_level = df['water_level'].iloc[-1]
        current_time = df['datetime'].iloc[-1]
        
        # Tính toán đỉnh triều
        peaks_high, peaks_low = self._find_tide_peaks(df)
        
        # Dự báo đỉnh triều tiếp theo
        next_high_tide = self._predict_next_peak(df, peaks_high, peak_type='high')
        next_low_tide = self._predict_next_peak(df, peaks_low, peak_type='low')
        
        # Kiểm tra cảnh báo
        alert_level, alert_message = self._check_alert(
            current_level, 
            station_info
        )
        
        # Tính toán xu hướng
        trend = self._calculate_trend(df)
        
        # Thống kê
        stats = self._calculate_statistics(df)
        
        return {
            "station_id": station_id,
            "station_name": station_info['name'],
            "station_name_en": station_info['name_en'],
            "coordinates": station_info['coordinates'],
            "current": {
                "water_level": round(float(current_level), 2),
                "timestamp": current_time.isoformat(),
                "timestamp_vn": self._format_time_vn(current_time),
                "unit": "m"
            },
            "forecast": {
                "next_high_tide": next_high_tide,
                "next_low_tide": next_low_tide
            },
            "alert": {
                "level": alert_level,
                "message": alert_message,
                "threshold_warning": station_info['warning_threshold'],
                "threshold_flood": station_info['flood_threshold']
            },
            "trend": trend,
            "statistics": stats,
            "data_points": self._format_data_points(df),
            "last_updated": datetime.now(self.timezone).isoformat()
        }
    
    def _convert_to_dataframe(self, data_points: List[Dict]) -> pd.DataFrame:
        """
        Chuyển đổi data points thành DataFrame với timezone
        """
        try:
            df = pd.DataFrame(data_points)
            
            # Chuyển timestamp (milliseconds) sang datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Chuyển sang múi giờ Việt Nam (UTC+7)
            df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert(self.timezone)
            
            # Đổi tên cột value thành water_level
            df['water_level'] = df['value']
            
            # Sắp xếp theo thời gian
            df = df.sort_values('datetime').reset_index(drop=True)
            
            logger.info(f"✓ Đã chuyển đổi {len(df)} điểm dữ liệu")
            return df
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi chuyển đổi DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _find_tide_peaks(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Tìm các đỉnh triều cao và thấp
        
        Returns:
            Tuple (peaks_high, peaks_low) - DataFrame chứa các đỉnh
        """
        try:
            water_levels = df['water_level'].values
            
            # Tìm local maxima (đỉnh cao)
            peaks_high_idx = []
            for i in range(1, len(water_levels) - 1):
                if water_levels[i] > water_levels[i-1] and water_levels[i] > water_levels[i+1]:
                    peaks_high_idx.append(i)
            
            # Tìm local minima (đỉnh thấp)
            peaks_low_idx = []
            for i in range(1, len(water_levels) - 1):
                if water_levels[i] < water_levels[i-1] and water_levels[i] < water_levels[i+1]:
                    peaks_low_idx.append(i)
            
            peaks_high = df.iloc[peaks_high_idx] if peaks_high_idx else pd.DataFrame()
            peaks_low = df.iloc[peaks_low_idx] if peaks_low_idx else pd.DataFrame()
            
            logger.info(f"✓ Tìm thấy {len(peaks_high)} đỉnh cao và {len(peaks_low)} đỉnh thấp")
            
            return peaks_high, peaks_low
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi tìm đỉnh triều: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _predict_next_peak(self, df: pd.DataFrame, peaks: pd.DataFrame, peak_type: str) -> Optional[Dict]:
        """
        Dự báo đỉnh triều tiếp theo dựa trên chu kỳ
        
        Args:
            df: DataFrame chứa dữ liệu
            peaks: DataFrame chứa các đỉnh đã tìm được
            peak_type: 'high' hoặc 'low'
        """
        if peaks.empty or len(peaks) < 2:
            return None
        
        try:
            # Tính chu kỳ trung bình giữa các đỉnh (trong giờ)
            time_diffs = peaks['datetime'].diff().dropna()
            avg_cycle = time_diffs.mean()
            
            # Đỉnh gần nhất
            last_peak = peaks.iloc[-1]
            last_peak_time = last_peak['datetime']
            last_peak_level = last_peak['water_level']
            
            # Dự báo thời gian đỉnh tiếp theo
            next_peak_time = last_peak_time + avg_cycle
            
            # Dự báo mực nước (trung bình của các đỉnh gần đây)
            recent_peaks_level = peaks['water_level'].tail(3).mean()
            
            return {
                "time": next_peak_time.isoformat(),
                "time_vn": self._format_time_vn(next_peak_time),
                "predicted_level": round(float(recent_peaks_level), 2),
                "type": "Triều cao" if peak_type == 'high' else "Triều thấp",
                "confidence": "medium"  # Độ tin cậy
            }
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi dự báo đỉnh triều: {str(e)}")
            return None
    
    def _check_alert(self, current_level: float, station_info: Dict) -> Tuple[str, str]:
        """
        Kiểm tra và tạo cảnh báo dựa trên mực nước hiện tại
        
        Returns:
            Tuple (alert_level, alert_message)
        """
        flood_threshold = station_info['flood_threshold']
        warning_threshold = station_info['warning_threshold']
        station_name = station_info['name']
        
        if current_level >= flood_threshold:
            return (
                "CRITICAL",
                f"🚨 CẢNH BÁO NGẬP LỤT! Mực nước tại {station_name} đạt {current_level}m, "
                f"vượt ngưỡng báo động III ({flood_threshold}m). Nguy cơ ngập úng nghiêm trọng!"
            )
        elif current_level >= warning_threshold:
            return (
                "WARNING",
                f"⚠️ Cảnh báo mực nước cao tại {station_name}: {current_level}m, "
                f"vượt ngưỡng cảnh báo ({warning_threshold}m). Cần theo dõi sát."
            )
        else:
            distance_to_warning = warning_threshold - current_level
            return (
                "NORMAL",
                f"✓ Mực nước tại {station_name} trong giới hạn an toàn: {current_level}m "
                f"(còn {distance_to_warning:.2f}m tới ngưỡng cảnh báo)."
            )
    
    def _calculate_trend(self, df: pd.DataFrame) -> Dict:
        """
        Tính toán xu hướng mực nước (đang lên hay xuống)
        """
        try:
            # Lấy 6 giờ gần nhất
            recent_df = df.tail(6)
            
            if len(recent_df) < 2:
                return {"direction": "unknown", "rate": 0}
            
            # Tính độ dốc (slope) bằng linear regression đơn giản
            x = np.arange(len(recent_df))
            y = recent_df['water_level'].values
            
            slope = np.polyfit(x, y, 1)[0]
            
            # Phân loại xu hướng
            if slope > 0.05:
                direction = "rising"
                direction_vn = "Đang lên"
            elif slope < -0.05:
                direction = "falling"
                direction_vn = "Đang xuống"
            else:
                direction = "stable"
                direction_vn = "Ổn định"
            
            return {
                "direction": direction,
                "direction_vn": direction_vn,
                "rate": round(float(slope), 4),
                "rate_description": f"{abs(slope*100):.2f} cm/giờ"
            }
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi tính xu hướng: {str(e)}")
            return {"direction": "unknown", "rate": 0}
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Tính toán thống kê cơ bản
        """
        try:
            return {
                "max": round(float(df['water_level'].max()), 2),
                "min": round(float(df['water_level'].min()), 2),
                "mean": round(float(df['water_level'].mean()), 2),
                "std": round(float(df['water_level'].std()), 2),
                "range": round(float(df['water_level'].max() - df['water_level'].min()), 2)
            }
        except Exception as e:
            logger.error(f"✗ Lỗi khi tính thống kê: {str(e)}")
            return {}
    
    def _format_data_points(self, df: pd.DataFrame, limit: int = 48) -> List[Dict]:
        """
        Format data points để trả về API (giới hạn số lượng)
        """
        try:
            # Lấy tối đa limit điểm gần nhất
            df_limited = df.tail(limit)
            
            points = []
            for _, row in df_limited.iterrows():
                points.append({
                    "timestamp": int(row['datetime'].timestamp() * 1000),
                    "datetime": row['datetime'].isoformat(),
                    "water_level": round(float(row['water_level']), 2)
                })
            
            return points
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi format data points: {str(e)}")
            return []
    
    def _format_time_vn(self, dt: datetime) -> str:
        """
        Format thời gian theo định dạng Việt Nam
        """
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    
    def process_all_stations(self, raw_data_dict: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Xử lý dữ liệu cho tất cả các trạm
        
        Args:
            raw_data_dict: Dict chứa dữ liệu thô của tất cả các trạm
            
        Returns:
            Dict chứa dữ liệu đã xử lý của tất cả các trạm
        """
        processed_data = {}
        
        for station_id, raw_data in raw_data_dict.items():
            logger.info(f"\nĐang xử lý dữ liệu trạm: {self.stations[station_id]['name']}")
            
            processed = self.process_station_data(raw_data)
            if processed:
                processed_data[station_id] = processed
                
                # Log thông tin cảnh báo
                alert = processed.get('alert', {})
                logger.info(f"  → {alert.get('message', 'N/A')}")
        
        return processed_data


def test_processor():
    """
    Hàm test data processor
    """
    import json
    from mrc_scraper import MRCWaterLevelScraper
    
    print("="*60)
    print("TESTING WATER LEVEL DATA PROCESSOR")
    print("="*60)
    
    # Scrape dữ liệu
    scraper = MRCWaterLevelScraper()
    raw_data = scraper.scrape_all_stations()
    
    # Xử lý dữ liệu
    processor = WaterLevelProcessor()
    processed_data = processor.process_all_stations(raw_data)
    
    print(f"\nĐã xử lý {len(processed_data)} trạm")
    print(json.dumps(processed_data, indent=2, ensure_ascii=False))
    
    return processed_data


if __name__ == "__main__":
    test_processor()

