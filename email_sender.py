"""
Email sender — Gmail SMTP qua env vars.
Cần set trong Railway Variables (hoặc .env local):
  MAIL_USERNAME  = your_gmail@gmail.com
  MAIL_PASSWORD  = your_gmail_app_password   (App Password, không phải mật khẩu thường)
  MAIL_FROM_NAME = SAFE GUARD               (tùy chọn)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('MAIL_USERNAME', '')
SMTP_PASS = os.environ.get('MAIL_PASSWORD', '')
FROM_NAME = os.environ.get('MAIL_FROM_NAME', 'SAFE GUARD')


def _send(to_email: str, subject: str, html_body: str) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        logger.warning('Email not sent: MAIL_USERNAME / MAIL_PASSWORD not configured')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{SMTP_USER}>'
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        logger.info(f'Email sent → {to_email}: {subject}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email → {to_email}: {e}')
        return False


def _otp_html(full_name: str, otp: str, is_resend: bool = False) -> str:
    intro = (
        'Đây là mã OTP mới cho tài khoản <strong>SAFE GUARD</strong> của bạn.'
        if is_resend else
        'Cảm ơn bạn đã đăng ký tài khoản <strong>SAFE GUARD</strong>.<br>'
        'Nhập mã OTP bên dưới trong ứng dụng để hoàn tất xác thực email.'
    )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#f4f7fb;padding:32px 16px;">
      <div style="background:#03045E;border-radius:16px 16px 0 0;padding:28px 32px;text-align:center;">
        <h1 style="color:#fff;font-size:24px;margin:0;letter-spacing:3px;">SAFE GUARD</h1>
        <p style="color:#90E0EF;margin:8px 0 0;font-size:14px;">Xác thực tài khoản</p>
      </div>
      <div style="background:#fff;border-radius:0 0 16px 16px;padding:36px 32px;">
        <p style="color:#2d3748;font-size:15px;">Xin chào <strong>{full_name}</strong>,</p>
        <p style="color:#4a5568;font-size:14px;line-height:1.6;">{intro}</p>
        <div style="text-align:center;margin:32px 0;">
          <div style="display:inline-block;background:#03045E;color:#fff;
                      font-size:36px;font-weight:bold;letter-spacing:12px;
                      padding:18px 36px;border-radius:12px;">{otp}</div>
        </div>
        <p style="color:#718096;font-size:13px;text-align:center;">
          Mã có hiệu lực trong <strong>10 phút</strong>.<br>
          Nếu bạn không yêu cầu, hãy bỏ qua email này.
        </p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#a0aec0;font-size:12px;text-align:center;">
          © 2024 SAFE GUARD – FPT University Cần Thơ
        </p>
      </div>
    </div>"""


def send_verification_otp(to_email: str, full_name: str, otp: str) -> bool:
    return _send(to_email, f'[SAFE GUARD] Mã xác thực email: {otp}',
                 _otp_html(full_name, otp, is_resend=False))


def send_resend_otp(to_email: str, full_name: str, otp: str) -> bool:
    return _send(to_email, f'[SAFE GUARD] Mã xác thực mới: {otp}',
                 _otp_html(full_name, otp, is_resend=True))
