"""
Database models and connection for user management
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta  # noqa: F401
from pathlib import Path
import json

class Database:
    """Database handler for user management"""
    
    def __init__(self, db_path=None):
        # DB_PATH env var cho phép trỏ tới Railway Volume (persistent storage)
        # VD: DB_PATH=/data/users.db  → dữ liệu không mất khi redeploy
        self.db_path = db_path or os.environ.get('DB_PATH', 'data/users.db')
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        # WAL mode allows concurrent reads alongside a single writer,
        # and busy_timeout retries instead of immediately raising "database is locked"
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                student_id TEXT UNIQUE,
                phone TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                last_login TEXT
            )
        ''')
        
        # Sessions table (for JWT tokens)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                refresh_token TEXT UNIQUE,
                device_info TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User activity logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # SOS reports (integrate with app functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sos_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                location_lat REAL NOT NULL,
                location_lon REAL NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # App usage statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                screen_name TEXT NOT NULL,
                duration_seconds INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Group codes — allow teams to login without individual accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                is_active INTEGER DEFAULT 1,
                max_members INTEGER,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')

        # FCM tokens for push notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fcm_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fcm_user ON fcm_tokens(user_id)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_fcm_token ON fcm_tokens(token)')

        # News articles (RSS crawled)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                link TEXT UNIQUE NOT NULL,
                published TEXT,
                source TEXT,
                category TEXT,
                image TEXT,
                fetched_at TEXT NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_published ON news(published DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)')

        # User real-time location sharing (Pro feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                share_token TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_loc_user ON user_locations(user_id)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_loc_token ON user_locations(share_token)')

        # Add group_code_id to users (idempotent)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN group_code_id INTEGER REFERENCES group_codes(id)')
        except Exception:
            pass

        # Email verification columns (idempotent)
        for col_def in [
            'ALTER TABLE users ADD COLUMN is_email_verified INTEGER DEFAULT 0',
            'ALTER TABLE users ADD COLUMN email_otp TEXT',
            'ALTER TABLE users ADD COLUMN email_otp_expires_at TEXT',
        ]:
            try:
                cursor.execute(col_def)
            except Exception:
                pass

        # Password reset OTP columns (idempotent)
        for col_def in [
            'ALTER TABLE users ADD COLUMN reset_otp TEXT',
            'ALTER TABLE users ADD COLUMN reset_otp_expires_at TEXT',
        ]:
            try:
                cursor.execute(col_def)
            except Exception:
                pass

        # Pro plan + SOS count (idempotent)
        for col_def in [
            'ALTER TABLE users ADD COLUMN is_pro INTEGER DEFAULT 0',
            'ALTER TABLE users ADD COLUMN sos_count INTEGER DEFAULT 0',
            'ALTER TABLE users ADD COLUMN pro_expires_at TEXT',
            'ALTER TABLE users ADD COLUMN sos_reset_at TEXT',
        ]:
            try:
                cursor.execute(col_def)
            except Exception:
                pass

        # Upgrade existing group_members to Pro (migration, no expiry)
        cursor.execute(
            "UPDATE users SET is_pro = 1 WHERE role = 'group_member' AND is_pro = 0"
        )

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_codes_code ON group_codes(code)')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity(user_id)')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if not exists
        self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE role = ?', ('admin',))
        if cursor.fetchone() is None:
            # Create admin with default password (should be changed)
            password_hash = self.hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (full_name, student_id, phone, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Admin',
                'ADMIN001',
                '0000000000',
                'admin@fptguard.com',
                password_hash,
                'admin',
                datetime.now().isoformat()
            ))
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def hash_password(password):
        """Hash password with SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    # User CRUD operations
    
    def create_user(self, full_name, student_id, phone, email, password, role='user'):
        """Create new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (full_name, student_id, phone, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, student_id, phone, email, password_hash, role, datetime.now().isoformat()))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            self.log_activity(user_id, 'user_created', None)
            
            return self.get_user_by_id(user_id)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'email' in str(e):
                raise ValueError('Email already exists')
            elif 'student_id' in str(e):
                raise ValueError('Student ID already exists')
            raise
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def verify_password(self, email, password):
        """Verify user password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        password_hash = self.hash_password(password)
        if password_hash == user['password_hash']:
            return user
        return None
    
    def update_user(self, user_id, **kwargs):
        """Update user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['full_name', 'student_id', 'phone', 'email', 'is_active', 'role']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        try:
            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'student_id' in str(e):
                raise ValueError('Mã số sinh viên này đã được sử dụng bởi tài khoản khác')
            elif 'email' in str(e):
                raise ValueError('Email này đã được sử dụng bởi tài khoản khác')
            raise
        finally:
            conn.close()
        return self.get_user_by_id(user_id)
    
    def get_all_users(self, limit=100, offset=0, role=None):
        """Get all users with pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if role:
            cursor.execute('''
                SELECT id, full_name, student_id, phone, email, role, is_active,
                       is_pro, pro_expires_at, sos_count, created_at, last_login
                FROM users WHERE role = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (role, limit, offset))
        else:
            cursor.execute('''
                SELECT id, full_name, student_id, phone, email, role, is_active,
                       is_pro, pro_expires_at, sos_count, created_at, last_login
                FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        users = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        cursor.execute('SELECT COUNT(*) as count FROM users' + (' WHERE role = ?' if role else ''),
                      (role,) if role else ())
        total = cursor.fetchone()['count']
        
        conn.close()
        return users, total
    
    # Session management
    
    def create_session(self, user_id, device_info=None, ip_address=None):
        """Create user session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        token = self.generate_token()
        refresh_token = self.generate_token()
        expires_at = datetime.now() + timedelta(days=7)  # Token valid for 7 days
        
        cursor.execute('''
            INSERT INTO sessions (user_id, token, refresh_token, device_info, ip_address, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, token, refresh_token, device_info, ip_address, 
              datetime.now().isoformat(), expires_at.isoformat()))
        
        conn.commit()
        
        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (datetime.now().isoformat(), user_id))
        conn.commit()
        
        conn.close()
        
        return {
            'token': token,
            'refresh_token': refresh_token,
            'expires_at': expires_at.isoformat()
        }
    
    def verify_token(self, token):
        """Verify session token. Returns (session_dict, error_code).
        error_code: None = OK, 'account_disabled' = user bị khóa hoặc group code bị tắt,
        None (with session None) = invalid/expired.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, u.id as user_id, u.email, u.role, u.is_active as user_is_active,
                   u.group_code_id,
                   gc.is_active as group_is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN group_codes gc ON u.group_code_id = gc.id
            WHERE s.token = ? AND s.is_active = 1
        ''', (token,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return (None, None)
        
        session = dict(row)
        # User bị khóa trực tiếp
        if not session.get('user_is_active', 1):
            return (None, 'account_disabled')

        # Group member mà group code bị tắt → coi như bị khóa
        if session.get('group_code_id') and not session.get('group_is_active', 1):
            return (None, 'account_disabled')
        
        # Check if expired
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            self.invalidate_session(token)
            return (None, None)
        
        session['user_id'] = session['user_id']
        session['email'] = session['email']
        session['role'] = session['role']
        return (session, None)
    
    def invalidate_session(self, token):
        """Invalidate session (logout)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE sessions SET is_active = 0 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    
    def refresh_session(self, refresh_token):
        """Refresh session token. Returns (new_session, error_code).
        error_code: None = OK, 'account_disabled' = user bị khóa hoặc group code bị tắt."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, u.is_active as user_is_active,
                   u.group_code_id,
                   gc.is_active as group_is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN group_codes gc ON u.group_code_id = gc.id
            WHERE s.refresh_token = ? AND s.is_active = 1
        ''', (refresh_token,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return (None, None)
        
        session = dict(row)
        if not session.get('user_is_active', 1):
            conn.close()
            return (None, 'account_disabled')

        if session.get('group_code_id') and not session.get('group_is_active', 1):
            conn.close()
            return (None, 'account_disabled')
        
        # Create new session
        new_session = self.create_session(session['user_id'],
                                          session['device_info'],
                                          session['ip_address'])
        cursor.execute('UPDATE sessions SET is_active = 0 WHERE refresh_token = ?',
                      (refresh_token,))
        conn.commit()
        conn.close()
        return (new_session, None)
    
    # Activity logging
    
    def log_activity(self, user_id, action, details=None, ip_address=None):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activity (user_id, action, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, json.dumps(details) if details else None,
              ip_address, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_activity(self, user_id, limit=50):
        """Get user activity logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_activity
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return activities
    
    # Analytics
    
    def get_user_statistics(self):
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        
        # Active users (logged in last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('SELECT COUNT(*) as active FROM users WHERE last_login >= ?',
                      (seven_days_ago,))
        active_users = cursor.fetchone()['active']
        
        # New users (created in last 7 days)
        cursor.execute('SELECT COUNT(*) as new FROM users WHERE created_at >= ?',
                      (seven_days_ago,))
        new_users = cursor.fetchone()['new']
        
        # Users by role
        cursor.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role')
        users_by_role = {row['role']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_7days': new_users,
            'users_by_role': users_by_role
        }
    
    def get_activity_statistics(self, days=7):
        """Get activity statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Most active users
        cursor.execute('''
            SELECT u.full_name, u.email, COUNT(a.id) as activity_count
            FROM user_activity a
            JOIN users u ON a.user_id = u.id
            WHERE a.created_at >= ?
            GROUP BY u.id
            ORDER BY activity_count DESC
            LIMIT 10
        ''', (since,))
        
        most_active = [dict(row) for row in cursor.fetchall()]
        
        # Activity by action
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM user_activity
            WHERE created_at >= ?
            GROUP BY action
            ORDER BY count DESC
        ''', (since,))
        
        activity_by_action = {row['action']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'most_active_users': most_active,
            'activity_by_action': activity_by_action
        }
    
    # SOS Reports
    
    def create_sos_report(self, user_id, location_lat, location_lon, message=None):
        """Create SOS report"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sos_reports (user_id, location_lat, location_lon, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, location_lat, location_lon, message, datetime.now().isoformat()))
        
        report_id = cursor.lastrowid
        conn.commit()
        
        # Log activity
        self.log_activity(user_id, 'sos_created', {'report_id': report_id})
        
        conn.close()
        return report_id
    
    def get_sos_reports(self, status=None, limit=100):
        """Get SOS reports"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT s.*, u.full_name, u.phone, u.email
                FROM sos_reports s
                JOIN users u ON s.user_id = u.id
                WHERE s.status = ?
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT s.*, u.full_name, u.phone, u.email
                FROM sos_reports s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', (limit,))
        
        reports = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return reports
    
    def update_sos_status(self, report_id, status):
        """Update SOS report status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sos_reports
            SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), report_id))
        
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # Group Codes
    # -------------------------------------------------------------------------

    def create_group_code(self, code, name, description=None, created_by=None,
                          max_members=None, expires_at=None):
        """Create a new group code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO group_codes (code, name, description, created_by, is_active,
                                        max_members, expires_at, created_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            ''', (code.upper(), name, description, created_by,
                  max_members, expires_at, datetime.now().isoformat()))
            group_id = cursor.lastrowid
            conn.commit()
            return self.get_group_code_by_id(group_id)
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"Group code '{code}' already exists")
        finally:
            conn.close()

    def get_group_code_by_id(self, group_id):
        """Get group code by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM group_codes WHERE id = ?', (group_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_group_code_by_code(self, code):
        """Get group code by code string"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM group_codes WHERE code = ?', (code.upper(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_group_codes(self):
        """Get all group codes with member count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.*, COUNT(u.id) as member_count
            FROM group_codes g
            LEFT JOIN users u ON u.group_code_id = g.id
            GROUP BY g.id
            ORDER BY g.created_at DESC
        ''')
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def update_group_code(self, group_id, **kwargs):
        """Update group code fields"""
        conn = self.get_connection()
        cursor = conn.cursor()
        allowed = ['name', 'description', 'is_active', 'max_members', 'expires_at']
        updates = [(f, v) for f, v in kwargs.items() if f in allowed]
        if updates:
            set_clause = ', '.join(f"{f} = ?" for f, _ in updates)
            values = [v for _, v in updates] + [group_id]
            cursor.execute(f"UPDATE group_codes SET {set_clause} WHERE id = ?", values)
            conn.commit()
        conn.close()
        return self.get_group_code_by_id(group_id)

    def delete_group_code(self, group_id):
        """Delete group code (hard delete — clears member links first)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET group_code_id = NULL WHERE group_code_id = ?', (group_id,))
        cursor.execute('DELETE FROM group_codes WHERE id = ?', (group_id,))
        conn.commit()
        conn.close()

    def group_login(self, code, nickname):
        """
        Login / register using a group code + nickname.
        Returns the user dict (creates one if nickname is new in this group).
        """
        group = self.get_group_code_by_code(code)
        if not group:
            raise ValueError("Mã nhóm không tồn tại")
        if not group['is_active']:
            raise ValueError("Mã nhóm đã bị vô hiệu hóa")
        if group['expires_at']:
            if datetime.now() > datetime.fromisoformat(group['expires_at']):
                raise ValueError("Mã nhóm đã hết hạn")

        # Check member limit
        if group['max_members']:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as cnt FROM users WHERE group_code_id = ?', (group['id'],))
            cnt = cursor.fetchone()['cnt']
            conn.close()
            if cnt >= group['max_members']:
                raise ValueError("Nhóm đã đầy thành viên")

        # Build a stable synthetic email for this member slot
        safe_nick = nickname.strip().lower().replace(' ', '_')
        synthetic_email = f"{safe_nick}__{group['code'].lower()}@group.local"

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (synthetic_email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user = dict(row)
            # Update display name if nickname changed capitalisation
            if user['full_name'] != nickname.strip():
                user = self.update_user(user['id'], full_name=nickname.strip())
        else:
            # Create new group-member user (no password)
            user = self.create_group_member(
                full_name=nickname.strip(),
                email=synthetic_email,
                group_code_id=group['id'],
            )
        return user

    # -------------------------------------------------------------------------
    # Email Verification OTP
    # -------------------------------------------------------------------------

    def generate_email_otp(self, user_id):
        """Generate a 6-digit OTP, store it (expires in 10 minutes) and return it."""
        import random
        otp = f"{random.randint(0, 999999):06d}"
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET email_otp = ?, email_otp_expires_at = ? WHERE id = ?',
            (otp, expires_at, user_id)
        )
        conn.commit()
        conn.close()
        return otp

    def verify_email_otp(self, email, otp):
        """Verify OTP for given email. Returns True on success, error string on failure."""
        user = self.get_user_by_email(email)
        if not user:
            return 'Email không tồn tại'
        if user.get('is_email_verified'):
            return True  # Already verified
        if user.get('email_otp') != otp:
            return 'Mã OTP không đúng'
        expires_at = user.get('email_otp_expires_at')
        if not expires_at or datetime.now() > datetime.fromisoformat(expires_at):
            return 'Mã OTP đã hết hạn (10 phút)'
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET is_email_verified = 1, email_otp = NULL, email_otp_expires_at = NULL WHERE id = ?',
            (user['id'],)
        )
        conn.commit()
        conn.close()
        return True

    # ── Password Reset OTP ───────────────────────────────────────────────────

    def generate_reset_otp(self, user_id):
        """Generate a 6-digit OTP for password reset (expires in 10 minutes)."""
        import random
        otp = f"{random.randint(0, 999999):06d}"
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET reset_otp = ?, reset_otp_expires_at = ? WHERE id = ?',
            (otp, expires_at, user_id)
        )
        conn.commit()
        conn.close()
        return otp

    def verify_reset_otp_and_change_password(self, email, otp, new_password):
        """Verify reset OTP, update password hash, clear OTP. Returns True or error string."""
        user = self.get_user_by_email(email)
        if not user:
            return 'Email không tồn tại'
        if user.get('reset_otp') != otp:
            return 'Mã OTP không đúng'
        expires_at = user.get('reset_otp_expires_at')
        if not expires_at or datetime.now() > datetime.fromisoformat(expires_at):
            return 'Mã OTP đã hết hạn (10 phút)'
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET password_hash = ?, reset_otp = NULL, reset_otp_expires_at = NULL WHERE id = ?',
            (new_hash, user['id'])
        )
        conn.commit()
        conn.close()
        return True

    def create_group_member(self, full_name, email, group_code_id):
        """Create a group-member user (passwordless). Group members are Pro by default."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (full_name, student_id, phone, email, password_hash,
                                   role, is_active, group_code_id, is_pro, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, 1, ?)
            ''', (full_name, None, '', email, '', 'group_member',
                  group_code_id, datetime.now().isoformat()))
            user_id = cursor.lastrowid
            conn.commit()
            return self.get_user_by_id(user_id)
        finally:
            conn.close()


    # ── Pro plan ─────────────────────────────────────────────────────────────

    FREE_SOS_LIMIT = 10

    def set_pro(self, user_id: int, is_pro: bool, months: int = 1):
        """Nâng/hạ Pro. Nếu is_pro=True thì set pro_expires_at = now + months tháng.
        group_member không có expiry (pro_expires_at = NULL).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_pro:
            expires_at = (datetime.now() + timedelta(days=30 * months)).isoformat()
            cursor.execute(
                'UPDATE users SET is_pro = 1, pro_expires_at = ? WHERE id = ?',
                (expires_at, user_id)
            )
        else:
            cursor.execute(
                'UPDATE users SET is_pro = 0, pro_expires_at = NULL WHERE id = ?',
                (user_id,)
            )
        conn.commit()
        conn.close()

    def expire_pro_accounts(self) -> list:
        """Hạ tất cả tài khoản Pro đã hết hạn về Free. Trả về list user bị hạ."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            '''SELECT id, full_name, email FROM users
               WHERE is_pro = 1 AND pro_expires_at IS NOT NULL AND pro_expires_at <= ?''',
            (now,)
        )
        expired = [dict(r) for r in cursor.fetchall()]
        if expired:
            ids = [u['id'] for u in expired]
            cursor.execute(
                f"UPDATE users SET is_pro = 0, pro_expires_at = NULL WHERE id IN ({','.join('?'*len(ids))})",
                ids
            )
            conn.commit()
        conn.close()
        return expired

    def can_send_sos(self, user_id: int) -> tuple[bool, int, int]:
        """Returns (allowed, used, limit). limit=-1 means unlimited (Pro).
        Free users get FREE_SOS_LIMIT per calendar month; count auto-resets.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT is_pro, sos_count, sos_reset_at FROM users WHERE id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, 0, self.FREE_SOS_LIMIT

        if row['is_pro']:
            conn.close()
            return True, row['sos_count'] or 0, -1

        now = datetime.now()
        reset_at = row['sos_reset_at']
        needs_reset = False
        if reset_at:
            try:
                last_reset = datetime.fromisoformat(reset_at)
                if last_reset.year != now.year or last_reset.month != now.month:
                    needs_reset = True
            except Exception:
                needs_reset = True
        else:
            # First time — initialise reset timestamp without touching sos_count
            needs_reset = True

        if needs_reset:
            cursor.execute(
                'UPDATE users SET sos_count = 0, sos_reset_at = ? WHERE id = ?',
                (now.isoformat(), user_id)
            )
            conn.commit()
            conn.close()
            return True, 0, self.FREE_SOS_LIMIT

        conn.close()
        used = row['sos_count'] or 0
        return used < self.FREE_SOS_LIMIT, used, self.FREE_SOS_LIMIT

    def increment_sos_count(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET sos_count = COALESCE(sos_count, 0) + 1 WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()

    def reset_free_sos_counts(self) -> int:
        """Reset sos_count = 0 cho tất cả tài khoản Free vào đầu tháng.
        Trả về số lượng user được reset."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET sos_count = 0, sos_reset_at = ? WHERE is_pro = 0",
            (now,)
        )
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    # ── FCM tokens ───────────────────────────────────────────────────────────

    def save_fcm_token(self, user_id: int, token: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO fcm_tokens (user_id, token, created_at) VALUES (?, ?, ?)',
            (user_id, token, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_fcm_tokens_for_user(self, user_id: int) -> list:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT token FROM fcm_tokens WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [r['token'] for r in rows]

    def get_all_admin_fcm_tokens(self) -> list:
        """All FCM tokens belonging to admin users (for SOS alerts)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT f.token FROM fcm_tokens f JOIN users u ON f.user_id = u.id WHERE u.role = 'admin'"
        )
        rows = cursor.fetchall()
        conn.close()
        return [r['token'] for r in rows]

    def delete_fcm_token(self, token: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM fcm_tokens WHERE token = ?', (token,))
        conn.commit()
        conn.close()

    # ── Real-time Location Sharing ────────────────────────────────────────────

    def upsert_user_location(self, user_id: int, latitude: float, longitude: float,
                             accuracy: float = None) -> str:
        """Upsert user's current location. Returns share_token."""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Check if exists → reuse token
        cursor.execute('SELECT share_token FROM user_locations WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            token = row['share_token']
            cursor.execute('''
                UPDATE user_locations
                SET latitude = ?, longitude = ?, accuracy = ?, updated_at = ?
                WHERE user_id = ?
            ''', (latitude, longitude, accuracy, datetime.now().isoformat(), user_id))
        else:
            token = secrets.token_urlsafe(16)
            cursor.execute('''
                INSERT INTO user_locations (user_id, latitude, longitude, accuracy, share_token, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, latitude, longitude, accuracy, token, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return token

    def get_location_by_token(self, token: str) -> dict:
        """Get location info by share_token (public, no auth needed)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ul.*, u.full_name FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.share_token = ?
        ''', (token,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ── SOS History ───────────────────────────────────────────────────────────

    def get_sos_history(self, user_id: int, limit: int = 20, offset: int = 0) -> tuple:
        """Return (list, total) of SOS reports for a user, newest first."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM sos_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (user_id, limit, offset)
        )
        reports = [dict(r) for r in cursor.fetchall()]
        cursor.execute('SELECT COUNT(*) as cnt FROM sos_reports WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()['cnt']
        conn.close()
        return reports, total

    # ── News (RSS) ────────────────────────────────────────────────────────────

    def save_news_articles(self, articles: list) -> int:
        """Bulk-insert news articles, skipping duplicates by link. Returns count inserted."""
        if not articles:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = 0
        for a in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news
                        (title, description, link, published, source, category, image, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    a.get('title', ''),
                    a.get('description', ''),
                    a.get('link', ''),
                    a.get('published', ''),
                    a.get('source', ''),
                    a.get('category', ''),
                    a.get('image'),
                    datetime.now().isoformat(),
                ))
                if cursor.rowcount:
                    inserted += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        return inserted

    def get_news(self, limit: int = 20, offset: int = 0, category: str = None) -> tuple:
        """Return (list_of_articles, total_count) ordered by published desc."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if category and category != 'Tất cả':
            cursor.execute(
                'SELECT * FROM news WHERE category = ? ORDER BY published DESC, fetched_at DESC LIMIT ? OFFSET ?',
                (category, limit, offset)
            )
            cursor2 = conn.cursor()
            cursor2.execute('SELECT COUNT(*) as cnt FROM news WHERE category = ?', (category,))
        else:
            cursor.execute(
                'SELECT * FROM news ORDER BY published DESC, fetched_at DESC LIMIT ? OFFSET ?',
                (limit, offset)
            )
            cursor2 = conn.cursor()
            cursor2.execute('SELECT COUNT(*) as cnt FROM news')
        articles = [dict(r) for r in cursor.fetchall()]
        total = cursor2.fetchone()['cnt']
        conn.close()
        return articles, total

    def get_news_categories(self) -> list:
        """Return distinct category values that have at least one article."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT DISTINCT category FROM news WHERE category IS NOT NULL AND category != "" ORDER BY category'
        )
        cats = [r['category'] for r in cursor.fetchall()]
        conn.close()
        return cats

    def cleanup_old_news(self, days: int = 30) -> int:
        """Delete articles older than `days` days. Returns count deleted."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('DELETE FROM news WHERE fetched_at < ?', (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


# Global database instance
db = Database()
