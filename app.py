"""
Flask API cho hệ thống giám sát mực nước sông Mekong
Flask REST API for Mekong River Water Level Monitoring
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import pytz

from scheduler import DataUpdateScheduler
from mrc_scraper import MRCWaterLevelScraper
from data_processor import WaterLevelProcessor
import config
from database import db
from auth import require_auth, require_admin, get_client_ip, get_device_info
from email_sender import send_verification_otp, send_resend_otp, send_pro_activated, send_pro_expired
from push_service import notify_sos, notify_pro_activated, notify_account_locked, send_push
import json as json_module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{config.LOGS_DIR}/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Khởi tạo Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Enable CORS cho Flutter app

# Khởi tạo scheduler
scheduler = DataUpdateScheduler()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    """
    Admin Dashboard - Web UI
    """
    return render_template('admin.html')


@app.route('/', methods=['GET'])
def home():
    """
    Endpoint trang chủ - thông tin API
    """
    return jsonify({
        "name": "FPT Guard 2.0 - Mekong River Monitoring API",
        "version": "2.0.0",
        "description": "API cung cấp dữ liệu mực nước sông Mekong và quản lý người dùng",
        "endpoints": {
            "general": {
                "/": "Thông tin API",
                "/api/health": "Health check"
            },
            "water_level": {
                "/api/stations": "Danh sách tất cả các trạm",
                "/api/stations/<station_id>": "Dữ liệu chi tiết của một trạm",
                "/api/latest": "Dữ liệu mới nhất của tất cả các trạm",
                "/api/alerts": "Danh sách cảnh báo hiện tại",
                "/api/historical/<station_id>": "Dữ liệu lịch sử của trạm",
                "/api/update": "Trigger cập nhật dữ liệu (POST)",
                "/api/status": "Trạng thái scheduler"
            },
            "authentication": {
                "/api/auth/register": "Đăng ký tài khoản (POST)",
                "/api/auth/login": "Đăng nhập (POST)",
                "/api/auth/verify-email": "Xác thực email bằng OTP (POST, body: email + otp)",
                "/api/auth/resend-otp": "Gửi lại mã OTP (POST, body: email)",
                "/api/auth/group-login": "Đăng nhập bằng mã nhóm (POST, body: code + nickname)",
                "/api/auth/logout": "Đăng xuất (POST, requires auth)",
                "/api/auth/refresh": "Refresh token (POST)",
                "/api/auth/me": "Thông tin user hiện tại (GET, requires auth)",
                "/api/auth/update": "Cập nhật profile (PUT, requires auth)",
                "/api/recover-admin": "Mở khóa admin khi khóa nhầm (POST, body: recovery_key)"
            },
            "sos": {
                "/api/sos": "Tạo báo cáo SOS (POST, requires auth)"
            },
            "admin": {
                "/api/admin/backup": "Tải file database backup (GET, admin only)",
                "/api/admin/users": "Danh sách users (GET, admin only)",
                "/api/admin/users/<user_id>": "Chi tiết user (GET/PUT, admin only)",
                "/api/admin/statistics": "Thống kê hệ thống (GET, admin only)",
                "/api/admin/sos": "Danh sách SOS reports (GET, admin only)",
                "/api/admin/sos/<report_id>": "Cập nhật SOS (PUT, admin only)",
                "/api/admin/group-codes": "Quản lý mã nhóm (GET/POST, admin only)",
                "/api/admin/group-codes/<id>": "Cập nhật / xóa mã nhóm (PUT/DELETE, admin only)",
                "/admin": "Admin Dashboard (Web UI)"
            },
            "tracking": {
                "/api/activity/track": "Theo dõi hoạt động user (POST, requires auth)"
            },
            "news": {
                "/api/news": "Tin tức an ninh từ RSS (GET, ?limit=20&offset=0&category=...)",
                "/api/admin/news/refresh": "Crawl RSS ngay lập tức (POST, admin only)"
            }
        },
        "default_admin": {
            "email": "admin@fptguard.com",
            "password": "admin123",
            "note": "Vui lòng đổi mật khẩu sau khi đăng nhập lần đầu"
        },
        "documentation": "https://github.com/your-repo/fpt-guard-v2",
        "contact": "support@fptguard.com"
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(pytz.timezone(config.TIMEZONE)).isoformat(),
        "scheduler_running": scheduler.is_running
    })


@app.route('/api/stations', methods=['GET'])
def get_all_stations():
    """
    Lấy thông tin tất cả các trạm (không bao gồm dữ liệu chi tiết)
    """
    try:
        stations_info = {}
        for station_id, info in config.STATIONS.items():
            stations_info[station_id] = {
                "station_id": station_id,
                "name": info['name'],
                "name_en": info['name_en'],
                "coordinates": info['coordinates'],
                "thresholds": {
                    "warning": info['warning_threshold'],
                    "flood": info['flood_threshold']
                }
            }
        
        return jsonify({
            "success": True,
            "data": stations_info,
            "total": len(stations_info)
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách trạm: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/latest', methods=['GET'])
def get_latest_data():
    """
    Lấy dữ liệu mới nhất của tất cả các trạm
    """
    try:
        # Đọc từ file JSON
        if not os.path.exists(config.LATEST_DATA_FILE):
            return jsonify({
                "success": False,
                "error": "Chưa có dữ liệu. Vui lòng đợi lần cập nhật đầu tiên."
            }), 404
        
        with open(config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            "success": True,
            "data": data
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu mới nhất: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stations/<station_id>', methods=['GET'])
def get_station_data(station_id):
    """
    Lấy dữ liệu chi tiết của một trạm cụ thể
    """
    try:
        if station_id not in config.STATIONS:
            return jsonify({
                "success": False,
                "error": f"Không tìm thấy trạm với ID: {station_id}"
            }), 404
        
        # Đọc từ file JSON
        if not os.path.exists(config.LATEST_DATA_FILE):
            return jsonify({
                "success": False,
                "error": "Chưa có dữ liệu. Vui lòng đợi lần cập nhật đầu tiên."
            }), 404
        
        with open(config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        station_data = data['stations'].get(station_id)
        
        if not station_data:
            return jsonify({
                "success": False,
                "error": f"Không có dữ liệu cho trạm {station_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": station_data
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu trạm {station_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Lấy danh sách các cảnh báo hiện tại (chỉ trạm có mực nước cao)
    """
    try:
        if not os.path.exists(config.LATEST_DATA_FILE):
            return jsonify({
                "success": False,
                "error": "Chưa có dữ liệu"
            }), 404
        
        with open(config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        alerts = []
        
        for station_id, station_data in data['stations'].items():
            alert = station_data.get('alert', {})
            if alert.get('level') in ['WARNING', 'CRITICAL']:
                alerts.append({
                    "station_id": station_id,
                    "station_name": station_data['station_name'],
                    "alert_level": alert['level'],
                    "message": alert['message'],
                    "current_water_level": station_data['current']['water_level'],
                    "timestamp": station_data['current']['timestamp']
                })
        
        return jsonify({
            "success": True,
            "data": {
                "alerts": alerts,
                "total": len(alerts),
                "has_critical": any(a['alert_level'] == 'CRITICAL' for a in alerts)
            }
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách cảnh báo: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/update', methods=['POST'])
def trigger_update():
    """
    Trigger cập nhật dữ liệu thủ công
    """
    try:
        logger.info("Nhận request cập nhật dữ liệu thủ công")
        
        success = scheduler.update_data()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Cập nhật dữ liệu thành công",
                "timestamp": datetime.now(pytz.timezone(config.TIMEZONE)).isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Cập nhật dữ liệu thất bại"
            }), 500
        
    except Exception as e:
        logger.error(f"Lỗi khi trigger update: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Lấy trạng thái của scheduler và hệ thống
    """
    try:
        status = scheduler.get_status()
        
        # Thêm thông tin file
        data_file_exists = os.path.exists(config.LATEST_DATA_FILE)
        data_file_size = os.path.getsize(config.LATEST_DATA_FILE) if data_file_exists else 0
        
        last_update = None
        if data_file_exists:
            with open(config.LATEST_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_update = data.get('last_updated')
        
        status.update({
            "data_file_exists": data_file_exists,
            "data_file_size_bytes": data_file_size,
            "last_update": last_update,
            "current_time": datetime.now(pytz.timezone(config.TIMEZONE)).isoformat()
        })
        
        return jsonify({
            "success": True,
            "data": status
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/historical/<station_id>', methods=['GET'])
def get_historical_data(station_id):
    """
    Lấy dữ liệu lịch sử của một trạm (từ CSV)
    
    Query params:
    - limit: số lượng bản ghi tối đa (default: 100)
    """
    try:
        if station_id not in config.STATIONS:
            return jsonify({
                "success": False,
                "error": f"Không tìm thấy trạm với ID: {station_id}"
            }), 404
        
        if not os.path.exists(config.HISTORICAL_DATA_FILE):
            return jsonify({
                "success": False,
                "error": "Chưa có dữ liệu lịch sử"
            }), 404
        
        # Đọc CSV
        import pandas as pd
        df = pd.read_csv(config.HISTORICAL_DATA_FILE)
        
        # Filter theo station_id
        df_station = df[df['station_id'] == station_id]
        
        # Limit
        limit = int(request.args.get('limit', 100))
        df_station = df_station.tail(limit)
        
        # Convert to dict
        records = df_station.to_dict('records')
        
        return jsonify({
            "success": True,
            "data": {
                "station_id": station_id,
                "records": records,
                "total": len(records)
            }
        })
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu lịch sử: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Đăng ký user mới
    
    Body: {
        "full_name": "Nguyen Van A",
        "student_id": "SE123456",
        "phone": "0123456789",
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'student_id', 'phone', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate email format
        if '@' not in data['email']:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Create user
        user = db.create_user(
            full_name=data['full_name'],
            student_id=data['student_id'],
            phone=data['phone'],
            email=data['email'],
            password=data['password']
        )
        
        # Log activity
        db.log_activity(user['id'], 'registered', ip_address=get_client_ip())

        # Create session immediately after registration
        device_info = json_module.dumps(get_device_info())
        session = db.create_session(user['id'], device_info, get_client_ip())

        # Remove sensitive data
        user.pop('password_hash', None)

        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'token': session['token'],
                'refresh_token': session['refresh_token'],
                'expires_at': session['expires_at'],
                'message': 'Đăng ký thành công'
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Registration failed'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Đăng nhập
    
    Body: {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Verify credentials
        user = db.verify_password(email, password)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Check if user is active
        if not user['is_active']:
            return jsonify({
                'success': False,
                'error': 'Account is disabled'
            }), 403

        # Create session
        device_info = json_module.dumps(get_device_info())
        session = db.create_session(user['id'], device_info, get_client_ip())
        
        # Log activity
        db.log_activity(user['id'], 'logged_in', ip_address=get_client_ip())
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'token': session['token'],
                'refresh_token': session['refresh_token'],
                'expires_at': session['expires_at']
            }
        })
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    """
    Xác thực email bằng mã OTP 6 số.

    Body: { "email": "user@example.com", "otp": "123456" }
    """
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        otp   = (data.get('otp')   or '').strip()

        if not email or not otp:
            return jsonify({'success': False, 'error': 'email và otp là bắt buộc'}), 400

        result = db.verify_email_otp(email, otp)
        if result is not True:
            return jsonify({'success': False, 'error': result}), 400

        # Create session for auto-login after verification
        user = db.get_user_by_email(email)
        user.pop('password_hash', None)
        device_info = json_module.dumps(get_device_info())
        session = db.create_session(user['id'], device_info, get_client_ip())
        db.log_activity(user['id'], 'email_verified', ip_address=get_client_ip())

        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'token': session['token'],
                'refresh_token': session['refresh_token'],
                'expires_at': session['expires_at'],
            }
        })
    except Exception as e:
        logger.error(f'Error verifying email: {e}')
        return jsonify({'success': False, 'error': 'Xác thực thất bại'}), 500


@app.route('/api/auth/resend-otp', methods=['POST'])
def resend_otp():
    """
    Gửi lại mã OTP.

    Body: { "email": "user@example.com" }
    """
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'success': False, 'error': 'email là bắt buộc'}), 400

        user = db.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'Email không tồn tại'}), 404
        if user.get('is_email_verified'):
            return jsonify({'success': True, 'message': 'Email đã được xác thực'})

        otp = db.generate_email_otp(user['id'])
        sent, send_err = send_resend_otp(email, user['full_name'], otp)

        return jsonify({
            'success': True,
            'email_sent': sent,
            'email_error': send_err if not sent else None,
            'message': f'Đã gửi lại mã OTP đến {email}' if sent else f'Không gửi được email: {send_err}',
        })
    except Exception as e:
        logger.error(f'Error resending OTP: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/group-login', methods=['POST'])
def group_login():
    """
    Đăng nhập bằng mã nhóm (không cần email/password cá nhân).

    Body: {
        "code": "FPT2024",
        "nickname": "Nguyen Van A"
    }
    """
    try:
        data = request.get_json() or {}
        code = (data.get('code') or '').strip()
        nickname = (data.get('nickname') or '').strip()

        if not code or not nickname:
            return jsonify({'success': False, 'error': 'code và nickname là bắt buộc'}), 400
        if len(nickname) < 2:
            return jsonify({'success': False, 'error': 'Tên hiển thị phải có ít nhất 2 ký tự'}), 400

        user = db.group_login(code, nickname)

        device_info = json_module.dumps(get_device_info())
        session = db.create_session(user['id'], device_info, get_client_ip())
        db.log_activity(user['id'], 'group_login', {'code': code}, get_client_ip())

        user.pop('password_hash', None)
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'token': session['token'],
                'refresh_token': session['refresh_token'],
                'expires_at': session['expires_at'],
            }
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error during group login: {e}")
        return jsonify({'success': False, 'error': 'Đăng nhập thất bại'}), 500


@app.route('/api/recover-admin', methods=['POST'])
def recover_admin():
    """
    Mở khóa tài khoản admin khi bị khóa nhầm.
    Cần set biến môi trường ADMIN_RECOVERY_KEY (và tùy chọn ADMIN_EMAIL).
    Body: { "recovery_key": "your_secret" }
    """
    try:
        data = request.get_json() or {}
        recovery_key = data.get('recovery_key') or request.args.get('recovery_key')
        expected = os.environ.get('ADMIN_RECOVERY_KEY')
        if not expected or not recovery_key or recovery_key != expected:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing recovery key'
            }), 403
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@fptguard.com')
        user = db.get_user_by_email(admin_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Admin user not found'
            }), 404
        db.update_user(user['id'], is_active=1)
        logger.info(f"Admin account {admin_email} unlocked via recovery")
        return jsonify({
            'success': True,
            'message': 'Admin account has been unlocked. You can log in again.'
        })
    except Exception as e:
        logger.error(f"Error recovering admin: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Đăng xuất"""
    try:
        token = request.headers.get('Authorization').split()[1]
        db.invalidate_session(token)
        
        # Log activity
        db.log_activity(request.user_id, 'logged_out', ip_address=get_client_ip())
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token
    
    Body: {
        "refresh_token": "..."
    }
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'success': False,
                'error': 'Refresh token is required'
            }), 400
        
        new_session, error_code = db.refresh_session(refresh_token)
        
        if error_code == 'account_disabled':
            return jsonify({
                'success': False,
                'error': 'Account is disabled'
            }), 403
        
        if not new_session:
            return jsonify({
                'success': False,
                'error': 'Invalid refresh token'
            }), 401
        
        return jsonify({
            'success': True,
            'data': new_session
        })
        
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed'
        }), 500


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Lấy thông tin user hiện tại"""
    try:
        user = db.get_user_by_id(request.user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'data': user
        })
        
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/update', methods=['PUT'])
@require_auth
def update_profile():
    """
    Cập nhật thông tin profile
    
    Body: {
        "full_name": "...",
        "phone": "...",
        "student_id": "..."
    }
    """
    try:
        data = request.get_json()
        
        # Only allow updating certain fields
        allowed_fields = ['full_name', 'phone', 'student_id']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        user = db.update_user(request.user_id, **updates)
        
        # Log activity
        db.log_activity(request.user_id, 'profile_updated', updates, get_client_ip())
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'data': user
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.route('/api/admin/group-codes', methods=['GET'])
@require_admin
def admin_list_group_codes():
    """Danh sách tất cả mã nhóm (Admin only)"""
    try:
        codes = db.get_all_group_codes()
        return jsonify({'success': True, 'data': codes})
    except Exception as e:
        logger.error(f"Error listing group codes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/group-codes', methods=['POST'])
@require_admin
def admin_create_group_code():
    """
    Tạo mã nhóm mới (Admin only).

    Body: {
        "code": "FPT2024",
        "name": "Lớp SE1820",
        "description": "...",        // optional
        "max_members": 50,            // optional, null = unlimited
        "expires_at": "2025-12-31"    // optional ISO date
    }
    """
    try:
        data = request.get_json() or {}
        code = (data.get('code') or '').strip()
        name = (data.get('name') or '').strip()
        if not code or not name:
            return jsonify({'success': False, 'error': 'code và name là bắt buộc'}), 400

        group = db.create_group_code(
            code=code,
            name=name,
            description=data.get('description'),
            created_by=request.user_id,
            max_members=data.get('max_members'),
            expires_at=data.get('expires_at'),
        )
        db.log_activity(request.user_id, 'group_code_created', {'code': code}, get_client_ip())
        return jsonify({'success': True, 'data': group}), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating group code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/group-codes/<int:group_id>', methods=['PUT'])
@require_admin
def admin_update_group_code(group_id):
    """Cập nhật mã nhóm (Admin only)"""
    try:
        data = request.get_json() or {}
        group = db.update_group_code(group_id, **data)
        if not group:
            return jsonify({'success': False, 'error': 'Không tìm thấy mã nhóm'}), 404
        return jsonify({'success': True, 'data': group})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/group-codes/<int:group_id>', methods=['DELETE'])
@require_admin
def admin_delete_group_code(group_id):
    """Xóa mã nhóm (Admin only)"""
    try:
        db.delete_group_code(group_id)
        db.log_activity(request.user_id, 'group_code_deleted',
                       {'group_id': group_id}, get_client_ip())
        return jsonify({'success': True, 'message': 'Đã xóa mã nhóm'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/backup', methods=['GET'])
@require_admin
def admin_backup_db():
    """
    Tải file database (backup) - Admin only.
    GET /api/admin/backup
    Header: Authorization: Bearer <admin_token>
    """
    try:
        db_path = db.db_path
        if not os.path.isfile(db_path):
            return jsonify({'success': False, 'error': 'Database file not found'}), 404
        filename = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        return send_file(
            db_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        logger.error(f"Error backing up database: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_get_users():
    """
    Lấy danh sách tất cả users (Admin only)
    
    Query params:
    - limit: số lượng users mỗi trang (default: 100)
    - offset: vị trí bắt đầu (default: 0)
    - role: filter theo role (optional)
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        role = request.args.get('role')
        
        users, total = db.get_all_users(limit, offset, role)
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def admin_get_user(user_id):
    """Lấy thông tin chi tiết một user (Admin only)"""
    try:
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        # Get user activity
        activity = db.get_user_activity(user_id, limit=20)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'recent_activity': activity
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@require_admin
def admin_update_user(user_id):
    """
    Cập nhật thông tin user (Admin only)
    
    Body: {
        "full_name": "...",
        "phone": "...",
        "email": "...",
        "role": "user|admin",
        "is_active": true|false
    }
    """
    try:
        data = request.get_json()
        
        user = db.update_user(user_id, **data)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Log activity
        db.log_activity(request.user_id, 'admin_updated_user', 
                       {'target_user_id': user_id, 'updates': data},
                       get_client_ip())
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'data': user
        })
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/statistics', methods=['GET'])
@require_admin
def admin_get_statistics():
    """Lấy thống kê tổng quan (Admin only)"""
    try:
        user_stats = db.get_user_statistics()
        activity_stats = db.get_activity_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'users': user_stats,
                'activity': activity_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# SOS ENDPOINTS
# ============================================================================

@app.route('/api/sos', methods=['POST'])
@require_auth
def create_sos():
    """
    Tạo báo cáo SOS.
    Free: tối đa 10 lần. Pro: không giới hạn.

    Body: { "latitude": 10.123, "longitude": 105.456, "message": "Need help!" }
    """
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        message = data.get('message', '')

        if not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Location coordinates are required'}), 400

        # Check SOS quota
        allowed, used, limit = db.can_send_sos(request.user_id)
        if not allowed:
            return jsonify({
                'success': False,
                'error': f'Bạn đã dùng hết {limit} lần SOS miễn phí. Nâng cấp Pro để gửi không giới hạn.',
                'quota_exceeded': True,
                'sos_used': used,
                'sos_limit': limit,
            }), 403

        report_id = db.create_sos_report(
            user_id=request.user_id,
            location_lat=latitude,
            location_lon=longitude,
            message=message
        )
        db.increment_sos_count(request.user_id)

        # Push notification → all admin devices
        user = db.get_user_by_id(request.user_id)
        admin_tokens = db.get_all_admin_fcm_tokens()
        if admin_tokens and user:
            location_str = f'{latitude:.5f}, {longitude:.5f}'
            notify_sos(admin_tokens, user.get('full_name', 'Unknown'), location_str, message)

        _, used_now, _ = db.can_send_sos(request.user_id)
        remaining = (limit - used_now) if limit != -1 else -1

        return jsonify({
            'success': True,
            'data': {
                'report_id': report_id,
                'message': 'SOS report created successfully',
                'sos_used': used_now,
                'sos_remaining': remaining,
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating SOS report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/fcm-token', methods=['POST'])
@require_auth
def save_fcm_token():
    """Lưu FCM token cho push notification. Body: { "token": "..." }"""
    try:
        data = request.get_json() or {}
        token = (data.get('token') or '').strip()
        if not token:
            return jsonify({'success': False, 'error': 'token là bắt buộc'}), 400
        db.save_fcm_token(request.user_id, token)
        return jsonify({'success': True, 'message': 'FCM token saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/set-pro', methods=['POST'])
@require_admin
def admin_set_pro(user_id):
    """Nâng/hạ gói Pro cho user (chỉ áp dụng role=user, không áp dụng group_member).
    Body: { "is_pro": true|false, "months": 1 }
    """
    try:
        data = request.get_json() or {}
        is_pro = bool(data.get('is_pro', True))
        months = int(data.get('months', 1))

        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Không tìm thấy user'}), 404

        db.set_pro(user_id, is_pro, months=months)
        db.log_activity(request.user_id, 'admin_set_pro',
                        {'target_user_id': user_id, 'is_pro': is_pro, 'months': months},
                        get_client_ip())

        if is_pro:
            # Lấy pro_expires_at vừa set
            updated_user = db.get_user_by_id(user_id)
            expires_at = updated_user.get('pro_expires_at', '')

            # Gửi email thông báo (chỉ user thường, không phải group_member)
            if user.get('role') != 'group_member' and user.get('email'):
                send_pro_activated(user['email'], user['full_name'], expires_at)

            # Push notification
            user_tokens = db.get_fcm_tokens_for_user(user_id)
            if user_tokens:
                notify_pro_activated(user_tokens)

            return jsonify({
                'success': True,
                'message': f'Đã nâng Pro cho {user["full_name"]} đến {expires_at[:10]}',
                'pro_expires_at': expires_at,
            })
        else:
            return jsonify({'success': True, 'message': f'Đã hạ {user["full_name"]} về Free'})

    except Exception as e:
        logger.error(f'admin_set_pro error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/sos', methods=['GET'])
@require_admin
def admin_get_sos_reports():
    """
    Lấy danh sách SOS reports (Admin only)
    
    Query params:
    - status: pending|resolved|cancelled
    - limit: số lượng (default: 100)
    """
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        reports = db.get_sos_reports(status, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'reports': reports,
                'total': len(reports)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting SOS reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/sos/<int:report_id>', methods=['PUT'])
@require_admin
def admin_update_sos(report_id):
    """
    Cập nhật trạng thái SOS report (Admin only)
    
    Body: {
        "status": "resolved|cancelled"
    }
    """
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'resolved', 'cancelled']:
            return jsonify({
                'success': False,
                'error': 'Invalid status'
            }), 400
        
        db.update_sos_status(report_id, status)
        
        # Log activity
        db.log_activity(request.user_id, 'admin_updated_sos',
                       {'report_id': report_id, 'status': status},
                       get_client_ip())
        
        return jsonify({
            'success': True,
            'message': 'SOS report updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating SOS report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# USER ACTIVITY TRACKING
# ============================================================================

@app.route('/api/activity/track', methods=['POST'])
@require_auth
def track_activity():
    """
    Theo dõi hoạt động của user trong app
    
    Body: {
        "action": "view_screen|click_button|...",
        "details": {...}
    }
    """
    try:
        data = request.get_json()
        action = data.get('action')
        details = data.get('details')
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        db.log_activity(request.user_id, action, details, get_client_ip())
        
        return jsonify({
            'success': True,
            'message': 'Activity tracked'
        })
        
    except Exception as e:
        logger.error(f"Error tracking activity: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# ============================================================================
# NEWS ENDPOINTS
# ============================================================================

@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Lấy danh sách tin tức an ninh từ RSS (có phân trang + lọc danh mục).
    Query params:
      - limit  (int, default 20)
      - offset (int, default 0)
      - category (str, optional – 'Tất cả' or specific category)
    """
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category', None)

        articles, total = db.get_news(limit=limit, offset=offset, category=category)
        categories = db.get_news_categories()

        # If DB is empty, trigger a background crawl (non-blocking)
        if total == 0:
            import threading
            t = threading.Thread(target=scheduler.fetch_rss_news, daemon=True)
            t.start()

        return jsonify({
            "success": True,
            "news": articles,
            "total": total,
            "limit": limit,
            "offset": offset,
            "categories": categories,
        })
    except Exception as e:
        logger.error(f'get_news error: {e}', exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/admin/news/refresh', methods=['POST'])
@require_admin
def admin_refresh_news():
    """Kích hoạt crawl RSS ngay lập tức (admin only)."""
    try:
        scheduler.fetch_rss_news()
        _, total = db.get_news(limit=1, offset=0)
        return jsonify({"success": True, "message": f"Đã cập nhật tin tức. Tổng: {total} bài."})
    except Exception as e:
        logger.error(f'admin_refresh_news error: {e}', exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint không tồn tại"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Lỗi server"
    }), 500


# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Khởi động Flask app và scheduler
    """
    logger.info("="*70)
    logger.info("MEKONG RIVER WATER LEVEL MONITORING - API SERVER")
    logger.info("="*70)
    
    # Tạo thư mục nếu chưa có
    Path(config.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(config.LOGS_DIR).mkdir(parents=True, exist_ok=True)
    
    # Khởi động scheduler (disabled on Railway - no Chrome browser)
    logger.info("\nScheduler: DISABLED (Railway không hỗ trợ Chrome/Selenium)")
    logger.info("  → Dữ liệu có thể load từ file tĩnh hoặc cập nhật manual qua /api/admin/update")
    # scheduler.start(immediate=False)  # Tạm disable trên Railway

    # Khởi động RSS news scheduler (không cần Chrome, chỉ cần HTTP)
    try:
        from apscheduler.schedulers.background import BackgroundScheduler as _BGS
        from apscheduler.triggers.interval import IntervalTrigger as _IT
        import pytz as _pytz
        _news_scheduler = _BGS(timezone=_pytz.timezone(config.TIMEZONE))
        _news_scheduler.add_job(
            func=scheduler.fetch_rss_news,
            trigger=_IT(minutes=30),
            id='rss_news',
            name='RSS News Crawler',
            replace_existing=True,
        )
        _news_scheduler.start()
        logger.info("✓ RSS News scheduler đã khởi động (mỗi 30 phút)")
        # Crawl ngay lần đầu trong thread riêng (không block startup)
        import threading
        threading.Thread(target=scheduler.fetch_rss_news, daemon=True).start()
        logger.info("  → Đang crawl RSS lần đầu ở background...")
    except Exception as _e:
        logger.warning(f"RSS scheduler khởi động thất bại: {_e}")
    
    # Lấy port từ environment variable (cho cloud platforms) hoặc dùng config
    port = int(os.environ.get('PORT', config.API_PORT))
    host = os.environ.get('HOST', config.API_HOST)
    
    # Khởi động Flask app
    logger.info(f"\nKhởi động Flask API server...")
    logger.info(f"  → Host: {host}")
    logger.info(f"  → Port: {port}")
    logger.info(f"  → API URL: http://localhost:{port}")
    logger.info(f"  → Debug mode: {config.API_DEBUG}")
    logger.info(f"\n{'='*70}\n")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=config.API_DEBUG,
            use_reloader=False  # Tắt reloader để tránh chạy scheduler 2 lần
        )
    except KeyboardInterrupt:
        logger.info("\n\nNhận được tín hiệu dừng...")
        scheduler.stop()
        logger.info("API server đã dừng. Tạm biệt!")


if __name__ == '__main__':
    main()

