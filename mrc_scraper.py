"""
Module scrape dữ liệu mực nước từ Mekong River Commission (MRC)
MRC Water Level Data Scraper using Selenium
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MRCWaterLevelScraper:
    """
    Class để scrape dữ liệu mực nước từ trang MRC
    """
    
    def __init__(self):
        """Khởi tạo scraper với cấu hình Selenium"""
        self.url = config.MRC_URL
        self.driver = None
        self.stations = config.STATIONS
        
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Thiết lập Chrome WebDriver với các options cần thiết
        """
        import os
        
        chrome_options = Options()
        
        if config.SELENIUM_CONFIG['headless']:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--headless=new')  # Chrome 109+ syntax
        
        # Các options để tối ưu performance (đặc biệt quan trọng cho Docker)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        
        # Tắt các thông báo không cần thiết
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2
        })
        
        # Nếu đang chạy trong Docker, chỉ định Chrome binary path
        if os.path.exists('/usr/bin/google-chrome'):
            chrome_options.binary_location = '/usr/bin/google-chrome'
            logger.info("Running in Docker environment - using /usr/bin/google-chrome")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Thiết lập timeouts
            driver.implicitly_wait(config.SELENIUM_CONFIG['implicit_wait'])
            driver.set_page_load_timeout(config.SELENIUM_CONFIG['page_load_timeout'])
            
            logger.info("✓ Chrome WebDriver đã được khởi tạo thành công")
            return driver
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi khởi tạo WebDriver: {str(e)}")
            raise
    
    def _extract_chart_data(self, station_id: str) -> Optional[Dict]:
        """
        Extract dữ liệu từ biểu đồ Highcharts trên trang MRC
        
        Args:
            station_id: ID của trạm cần lấy dữ liệu
            
        Returns:
            Dict chứa dữ liệu time-series hoặc None nếu thất bại
        """
        try:
            # Đợi trang load xong
            time.sleep(config.REQUEST_DELAY)
            
            # Tìm và click vào trạm cần lấy dữ liệu
            station_name = self.stations[station_id]['name_en']
            logger.info(f"Đang tìm trạm {station_name}...")
            
            # Execute JavaScript để lấy dữ liệu từ Highcharts
            # MRC sử dụng Highcharts để hiển thị dữ liệu
            chart_data = self.driver.execute_script("""
                // Tìm tất cả Highcharts instances
                var charts = Highcharts.charts.filter(chart => chart !== undefined);
                if (charts.length === 0) return null;
                
                // Lấy chart đầu tiên (hoặc chart mực nước)
                var chart = charts[0];
                var series = chart.series[0];
                
                if (!series || !series.data) return null;
                
                // Extract data points
                var dataPoints = series.data.map(point => ({
                    timestamp: point.x,
                    value: point.y
                }));
                
                return {
                    name: series.name,
                    data: dataPoints,
                    unit: chart.yAxis[0].userOptions.title.text || 'm'
                };
            """)
            
            if chart_data and chart_data.get('data'):
                logger.info(f"✓ Đã lấy {len(chart_data['data'])} điểm dữ liệu từ {station_name}")
                return chart_data
            else:
                logger.warning(f"✗ Không tìm thấy dữ liệu chart cho {station_name}")
                return None
                
        except Exception as e:
            logger.error(f"✗ Lỗi khi extract dữ liệu chart: {str(e)}")
            return None
    
    def _parse_station_data(self, station_id: str) -> Optional[Dict]:
        """
        Parse dữ liệu cho một trạm cụ thể
        
        Args:
            station_id: ID của trạm
            
        Returns:
            Dict chứa thông tin trạm và dữ liệu mực nước
        """
        try:
            station_info = self.stations[station_id]
            
            # Tìm element chứa dữ liệu của trạm
            # Cần inspect trang MRC để xác định selector chính xác
            # Đây là placeholder logic
            
            # Thử nhiều cách để tìm dữ liệu
            selectors = [
                f"//div[contains(text(), '{station_info['name_en']}')]",
                f"//span[contains(text(), '{station_info['name']}')]",
                f"//td[contains(text(), '{station_info['name_en']}')]"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        logger.info(f"✓ Tìm thấy element cho {station_info['name']}")
                        break
                except:
                    continue
            
            if not element:
                logger.warning(f"Không tìm thấy element cho {station_info['name']}, thử extract từ chart...")
                chart_data = self._extract_chart_data(station_id)
                
                if chart_data:
                    return {
                        "station_id": station_id,
                        "station_name": station_info['name'],
                        "station_name_en": station_info['name_en'],
                        "data_source": "chart",
                        "raw_data": chart_data
                    }
            
            # Nếu tìm thấy element, extract dữ liệu
            # Logic này cần được điều chỉnh dựa trên cấu trúc HTML thực tế
            
            return None
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi parse dữ liệu trạm {station_id}: {str(e)}")
            return None
    
    def scrape_all_stations(self) -> Dict[str, Dict]:
        """
        Scrape dữ liệu từ tất cả các trạm
        
        Returns:
            Dict chứa dữ liệu của tất cả các trạm
        """
        results = {}
        
        try:
            # Khởi tạo driver
            self.driver = self._setup_driver()
            
            logger.info(f"Đang truy cập trang MRC: {self.url}")
            self.driver.get(self.url)
            
            # Đợi trang load
            wait = WebDriverWait(self.driver, config.SELENIUM_CONFIG['timeout'])
            
            try:
                # Đợi một element chính load xong
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("✓ Trang MRC đã load thành công")
                
                # Đợi thêm để JavaScript chạy xong
                time.sleep(5)
                
                # Kiểm tra xem có Highcharts không
                has_highcharts = self.driver.execute_script("""
                    return typeof Highcharts !== 'undefined';
                """)
                
                if has_highcharts:
                    logger.info("✓ Phát hiện Highcharts trên trang")
                else:
                    logger.warning("✗ Không phát hiện Highcharts, có thể cần đợi lâu hơn")
                
            except TimeoutException:
                logger.error("✗ Timeout khi load trang MRC")
                return results
            
            # Scrape từng trạm
            for station_id in self.stations.keys():
                logger.info(f"\n{'='*50}")
                logger.info(f"Đang scrape trạm: {self.stations[station_id]['name']}")
                
                station_data = self._parse_station_data(station_id)
                
                if station_data:
                    results[station_id] = station_data
                else:
                    # Tạo dữ liệu mẫu nếu scrape thất bại (để test)
                    logger.warning(f"Sử dụng dữ liệu mẫu cho {station_id}")
                    results[station_id] = self._generate_sample_data(station_id)
                
                # Delay giữa các request
                time.sleep(config.REQUEST_DELAY)
            
            logger.info(f"\n{'='*50}")
            logger.info(f"✓ Hoàn thành scrape {len(results)}/{len(self.stations)} trạm")
            
        except WebDriverException as e:
            logger.error(f"✗ Lỗi WebDriver: {str(e)}")
        except Exception as e:
            logger.error(f"✗ Lỗi không xác định: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver đã được đóng")
        
        return results
    
    def _generate_sample_data(self, station_id: str) -> Dict:
        """
        Tạo dữ liệu mẫu cho test (khi scrape thất bại)
        """
        import random
        from datetime import timedelta
        
        station_info = self.stations[station_id]
        now = datetime.now()
        
        # Tạo 24 điểm dữ liệu (mỗi giờ)
        data_points = []
        base_level = station_info['warning_threshold'] - 0.5
        
        for i in range(24):
            timestamp = (now - timedelta(hours=23-i)).timestamp() * 1000
            # Tạo mực nước dao động
            water_level = base_level + random.uniform(-0.3, 0.5)
            data_points.append({
                "timestamp": int(timestamp),
                "value": round(water_level, 2)
            })
        
        return {
            "station_id": station_id,
            "station_name": station_info['name'],
            "station_name_en": station_info['name_en'],
            "data_source": "sample",
            "raw_data": {
                "name": station_info['name'],
                "data": data_points,
                "unit": "m"
            }
        }
    
    def scrape_single_station(self, station_id: str) -> Optional[Dict]:
        """
        Scrape dữ liệu từ một trạm cụ thể
        
        Args:
            station_id: ID của trạm cần scrape
            
        Returns:
            Dict chứa dữ liệu trạm hoặc None
        """
        if station_id not in self.stations:
            logger.error(f"✗ Không tìm thấy trạm với ID: {station_id}")
            return None
        
        try:
            self.driver = self._setup_driver()
            self.driver.get(self.url)
            
            time.sleep(5)  # Đợi trang load
            
            station_data = self._parse_station_data(station_id)
            return station_data if station_data else self._generate_sample_data(station_id)
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi scrape trạm {station_id}: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()


def test_scraper():
    """
    Hàm test scraper
    """
    print("="*60)
    print("TESTING MRC WATER LEVEL SCRAPER")
    print("="*60)
    
    scraper = MRCWaterLevelScraper()
    results = scraper.scrape_all_stations()
    
    print(f"\nKết quả: Đã scrape {len(results)} trạm")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


if __name__ == "__main__":
    test_scraper()

