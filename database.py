"""
Database models and connection for user management
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import json

class Database:
    """Database handler for user management"""
    
    def __init__(self, db_path="data/users.db"):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
        
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        return self.get_user_by_id(user_id)
    
    def get_all_users(self, limit=100, offset=0, role=None):
        """Get all users with pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if role:
            cursor.execute('''
                SELECT id, full_name, student_id, phone, email, role, is_active, created_at, last_login
                FROM users WHERE role = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (role, limit, offset))
        else:
            cursor.execute('''
                SELECT id, full_name, student_id, phone, email, role, is_active, created_at, last_login
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
        """Verify session token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.id as user_id, u.email, u.role, u.is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.is_active = 1
        ''', (token,))
        
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            return None
        
        session = dict(session)
        
        # Check if expired
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            self.invalidate_session(token)
            return None
        
        # Check if user is active
        if not session['is_active']:
            return None
        
        return session
    
    def invalidate_session(self, token):
        """Invalidate session (logout)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE sessions SET is_active = 0 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    
    def refresh_session(self, refresh_token):
        """Refresh session token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE refresh_token = ? AND is_active = 1',
                      (refresh_token,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return None
        
        session = dict(session)
        
        # Create new session
        new_session = self.create_session(session['user_id'], 
                                          session['device_info'],
                                          session['ip_address'])
        
        # Invalidate old session
        cursor.execute('UPDATE sessions SET is_active = 0 WHERE refresh_token = ?',
                      (refresh_token,))
        conn.commit()
        conn.close()
        
        return new_session
    
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


# Global database instance
db = Database()
