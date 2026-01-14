"""
Flask API cho hệ thống giám sát mực nước sông Mekong
Flask REST API for Mekong River Water Level Monitoring
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pytz

from scheduler import DataUpdateScheduler
from mrc_scraper import MRCWaterLevelScraper
from data_processor import WaterLevelProcessor
import config
from database import db
from auth import require_auth, require_admin, get_client_ip, get_device_info
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
                "/api/auth/logout": "Đăng xuất (POST, requires auth)",
                "/api/auth/refresh": "Refresh token (POST)",
                "/api/auth/me": "Thông tin user hiện tại (GET, requires auth)",
                "/api/auth/update": "Cập nhật profile (PUT, requires auth)"
            },
            "sos": {
                "/api/sos": "Tạo báo cáo SOS (POST, requires auth)"
            },
            "admin": {
                "/api/admin/users": "Danh sách users (GET, admin only)",
                "/api/admin/users/<user_id>": "Chi tiết user (GET/PUT, admin only)",
                "/api/admin/statistics": "Thống kê hệ thống (GET, admin only)",
                "/api/admin/sos": "Danh sách SOS reports (GET, admin only)",
                "/api/admin/sos/<report_id>": "Cập nhật SOS (PUT, admin only)",
                "/admin": "Admin Dashboard (Web UI)"
            },
            "tracking": {
                "/api/activity/track": "Theo dõi hoạt động user (POST, requires auth)"
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
        
        # Create session
        device_info = json_module.dumps(get_device_info())
        session = db.create_session(user['id'], device_info, get_client_ip())
        
        # Log activity
        db.log_activity(user['id'], 'registered', ip_address=get_client_ip())
        
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
        
        session = db.refresh_session(refresh_token)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Invalid refresh token'
            }), 401
        
        return jsonify({
            'success': True,
            'data': session
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
    Tạo báo cáo SOS
    
    Body: {
        "latitude": 10.123,
        "longitude": 105.456,
        "message": "Need help!"
    }
    """
    try:
        data = request.get_json()
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        message = data.get('message', '')
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'error': 'Location coordinates are required'
            }), 400
        
        report_id = db.create_sos_report(
            user_id=request.user_id,
            location_lat=latitude,
            location_lon=longitude,
            message=message
        )
        
        return jsonify({
            'success': True,
            'data': {
                'report_id': report_id,
                'message': 'SOS report created successfully'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating SOS report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
    
    # Khởi động scheduler
    logger.info("\nKhởi động scheduler...")
    scheduler.start(immediate=True)
    
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

