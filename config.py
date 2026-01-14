"""
Cấu hình cho hệ thống giám sát mực nước sông Mekong
Configuration for Mekong River water level monitoring system
"""

# URL của trang MRC
MRC_URL = "https://portal.mrcmekong.org/monitoring/river-monitoring-telemetry"

# Các trạm quan trắc chính ở ĐBSCL
STATIONS = {
    "can_tho": {
        "name": "Cần Thơ",
        "name_en": "Can Tho",
        "flood_threshold": 2.0,  # Ngưỡng báo động III (mét)
        "warning_threshold": 1.8,  # Ngưỡng cảnh báo
        "coordinates": {"lat": 10.0452, "lon": 105.7469}
    },
    "my_thuan": {
        "name": "Mỹ Thuận",
        "name_en": "My Thuan",
        "flood_threshold": 2.2,
        "warning_threshold": 2.0,
        "coordinates": {"lat": 10.2833, "lon": 105.9167}
    },
    "vinh_long": {
        "name": "Vĩnh Long",
        "name_en": "Vinh Long",
        "flood_threshold": 2.0,
        "warning_threshold": 1.8,
        "coordinates": {"lat": 10.2396, "lon": 105.9572}
    },
    "tan_chau": {
        "name": "Tân Châu",
        "name_en": "Tan Chau",
        "flood_threshold": 4.5,
        "warning_threshold": 4.0,
        "coordinates": {"lat": 10.8000, "lon": 105.2500}
    },
    "chau_doc": {
        "name": "Châu Đốc",
        "name_en": "Chau Doc",
        "flood_threshold": 4.0,
        "warning_threshold": 3.5,
        "coordinates": {"lat": 10.7054, "lon": 105.1114}
    }
}

# Cấu hình Selenium
SELENIUM_CONFIG = {
    "headless": True,
    "timeout": 30,  # Giây
    "implicit_wait": 10,
    "page_load_timeout": 30
}

# Cấu hình cập nhật dữ liệu
UPDATE_INTERVAL = 3600  # Cập nhật mỗi 1 giờ (giây)

# Cấu hình lưu trữ
DATA_DIR = "data"
LOGS_DIR = "logs"
LATEST_DATA_FILE = "data/latest_water_levels.json"
HISTORICAL_DATA_FILE = "data/historical_data.csv"

# Múi giờ
TIMEZONE = "Asia/Ho_Chi_Minh"  # UTC+7

# Cấu hình Flask API
API_HOST = "0.0.0.0"
API_PORT = 5000
API_DEBUG = True

# Fallback API (dự phòng nếu MRC thất bại)
FALLBACK_APIS = {
    "stormglass": {
        "enabled": False,
        "api_key": "",  # Cần đăng ký tại https://stormglass.io/
        "url": "https://api.stormglass.io/v2/tide/extremes/point"
    }
}

# Delay giữa các request (tuân thủ đạo đức web scraping)
REQUEST_DELAY = 2  # Giây

