"""
Module scheduler để cập nhật dữ liệu định kỳ
Scheduler for periodic data updates
"""

import os
import json
import logging
import time
import csv
from datetime import datetime
from typing import Dict
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from mrc_scraper import MRCWaterLevelScraper
from data_processor import WaterLevelProcessor
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{config.LOGS_DIR}/scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataUpdateScheduler:
    """
    Class quản lý việc cập nhật dữ liệu định kỳ
    """
    
    def __init__(self):
        """Khởi tạo scheduler"""
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone(config.TIMEZONE))
        self.scraper = MRCWaterLevelScraper()
        self.processor = WaterLevelProcessor()
        self.is_running = False
        
        # Tạo thư mục nếu chưa tồn tại
        Path(config.DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(config.LOGS_DIR).mkdir(parents=True, exist_ok=True)
        
        logger.info("✓ DataUpdateScheduler đã được khởi tạo")
    
    def update_data(self):
        """
        Hàm chính để cập nhật dữ liệu từ MRC
        """
        try:
            logger.info("="*60)
            logger.info("BẮT ĐẦU CẬP NHẬT DỮ LIỆU MỰC NƯỚC")
            logger.info("="*60)
            
            start_time = time.time()
            
            # Bước 1: Scrape dữ liệu từ MRC
            logger.info("\n[1/4] Đang scrape dữ liệu từ MRC...")
            raw_data = self.scraper.scrape_all_stations()
            
            if not raw_data:
                logger.error("✗ Không lấy được dữ liệu từ MRC")
                return False
            
            logger.info(f"✓ Đã scrape {len(raw_data)} trạm")
            
            # Bước 2: Xử lý dữ liệu
            logger.info("\n[2/4] Đang xử lý dữ liệu...")
            processed_data = self.processor.process_all_stations(raw_data)
            
            if not processed_data:
                logger.error("✗ Không xử lý được dữ liệu")
                return False
            
            logger.info(f"✓ Đã xử lý {len(processed_data)} trạm")
            
            # Bước 3: Lưu dữ liệu mới nhất vào JSON
            logger.info("\n[3/4] Đang lưu dữ liệu vào JSON...")
            self._save_latest_data(processed_data)
            
            # Bước 4: Append vào file CSV lịch sử
            logger.info("\n[4/4] Đang cập nhật dữ liệu lịch sử CSV...")
            self._append_to_historical_data(processed_data)
            
            elapsed_time = time.time() - start_time
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ CẬP NHẬT HOÀN TẤT trong {elapsed_time:.2f} giây")
            logger.info(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi cập nhật dữ liệu: {str(e)}", exc_info=True)
            return False
    
    def _save_latest_data(self, processed_data: Dict):
        """
        Lưu dữ liệu mới nhất vào file JSON
        """
        try:
            # Thêm metadata
            output_data = {
                "last_updated": datetime.now(pytz.timezone(config.TIMEZONE)).isoformat(),
                "stations": processed_data,
                "metadata": {
                    "total_stations": len(processed_data),
                    "data_source": "Mekong River Commission (MRC)",
                    "update_interval_seconds": config.UPDATE_INTERVAL
                }
            }
            
            # Lưu file
            with open(config.LATEST_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Đã lưu dữ liệu vào {config.LATEST_DATA_FILE}")
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi lưu JSON: {str(e)}")
    
    def _append_to_historical_data(self, processed_data: Dict):
        """
        Append dữ liệu vào file CSV lịch sử
        """
        try:
            file_exists = os.path.exists(config.HISTORICAL_DATA_FILE)
            
            with open(config.HISTORICAL_DATA_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Viết header nếu file mới
                if not file_exists:
                    writer.writerow([
                        'timestamp',
                        'station_id',
                        'station_name',
                        'water_level',
                        'alert_level',
                        'trend_direction'
                    ])
                
                # Viết dữ liệu cho từng trạm
                timestamp = datetime.now(pytz.timezone(config.TIMEZONE)).isoformat()
                
                for station_id, data in processed_data.items():
                    writer.writerow([
                        timestamp,
                        station_id,
                        data['station_name'],
                        data['current']['water_level'],
                        data['alert']['level'],
                        data['trend']['direction']
                    ])
            
            logger.info(f"✓ Đã cập nhật dữ liệu lịch sử vào {config.HISTORICAL_DATA_FILE}")
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi lưu CSV: {str(e)}")
    
    def start(self, immediate: bool = True):
        """
        Khởi động scheduler
        
        Args:
            immediate: Nếu True, chạy update ngay lập tức trước khi bắt đầu schedule
        """
        if self.is_running:
            logger.warning("Scheduler đã đang chạy")
            return
        
        logger.info("="*60)
        logger.info("KHỞI ĐỘNG SCHEDULER")
        logger.info("="*60)
        
        # Chạy ngay lần đầu nếu immediate=True
        if immediate:
            logger.info("\nChạy cập nhật dữ liệu ban đầu...")
            self.update_data()
        
        # Thiết lập job định kỳ
        interval_minutes = config.UPDATE_INTERVAL // 60
        
        self.scheduler.add_job(
            func=self.update_data,
            trigger=IntervalTrigger(seconds=config.UPDATE_INTERVAL),
            id='update_water_level',
            name='Cập nhật mực nước từ MRC',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"\n✓ Scheduler đã khởi động")
        logger.info(f"  → Cập nhật mỗi {interval_minutes} phút ({config.UPDATE_INTERVAL} giây)")
        logger.info(f"  → Múi giờ: {config.TIMEZONE}")
        logger.info(f"  → Dữ liệu lưu tại: {config.DATA_DIR}")
        logger.info(f"{'='*60}\n")
    
    def stop(self):
        """
        Dừng scheduler
        """
        if not self.is_running:
            logger.warning("Scheduler chưa chạy")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("✓ Scheduler đã dừng")
    
    def get_status(self) -> Dict:
        """
        Lấy trạng thái của scheduler
        """
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            "is_running": self.is_running,
            "jobs": jobs,
            "update_interval_seconds": config.UPDATE_INTERVAL,
            "data_dir": config.DATA_DIR,
            "latest_data_file": config.LATEST_DATA_FILE
        }


def run_scheduler_standalone():
    """
    Chạy scheduler như một standalone service
    """
    logger.info("="*70)
    logger.info("MEKONG RIVER WATER LEVEL MONITORING - SCHEDULER SERVICE")
    logger.info("="*70)
    logger.info("Nhấn Ctrl+C để dừng service\n")
    
    scheduler = DataUpdateScheduler()
    
    try:
        # Khởi động scheduler
        scheduler.start(immediate=True)
        
        # Giữ chương trình chạy
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n\nNhận được tín hiệu dừng...")
        scheduler.stop()
        logger.info("Service đã dừng. Tạm biệt!")
    except Exception as e:
        logger.error(f"Lỗi: {str(e)}", exc_info=True)
        scheduler.stop()


if __name__ == "__main__":
    run_scheduler_standalone()

