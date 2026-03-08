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

def _send(to_email: str, subject: str, html_body: str) -> tuple[bool, str]:
    """Returns (success, error_message)"""
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('MAIL_USERNAME', '')
    smtp_pass = os.environ.get('MAIL_PASSWORD', '').replace(' ', '')
    from_name = os.environ.get('MAIL_FROM_NAME', 'SAFE GUARD')

    if not smtp_user or not smtp_pass:
        msg = 'MAIL_USERNAME / MAIL_PASSWORD chưa được cấu hình'
        logger.warning(f'Email not sent: {msg}')
        return False, msg
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{from_name} <{smtp_user}>'
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        logger.info(f'Email sent → {to_email}: {subject}')
        return True, ''
    except Exception as e:
        logger.error(f'Failed to send email → {to_email}: {e}')
        return False, str(e)


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


def send_pro_activated(to_email: str, full_name: str, expires_at: str) -> tuple[bool, str]:
    """Gửi email thông báo tài khoản được nâng lên Pro."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(expires_at)
        expires_str = dt.strftime('%d/%m/%Y')
    except Exception:
        expires_str = expires_at

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#f4f7fb;padding:32px 16px;">
      <div style="background:#03045E;border-radius:16px 16px 0 0;padding:28px 32px;text-align:center;">
        <h1 style="color:#fff;font-size:24px;margin:0;letter-spacing:3px;">SAFE GUARD</h1>
        <p style="color:#90E0EF;margin:8px 0 0;font-size:14px;">Thông báo nâng cấp tài khoản</p>
      </div>
      <div style="background:#fff;border-radius:0 0 16px 16px;padding:36px 32px;">
        <p style="color:#2d3748;font-size:15px;">Xin chào <strong>{full_name}</strong>,</p>
        <p style="color:#4a5568;font-size:14px;line-height:1.6;">
          Tài khoản của bạn đã được <strong>nâng cấp lên gói Pro</strong> bởi quản trị viên.
        </p>
        <div style="text-align:center;margin:28px 0;">
          <div style="display:inline-block;background:#03045E;color:#CAF0F8;
                      font-size:18px;font-weight:bold;padding:16px 32px;border-radius:12px;">
            ⭐ TÀI KHOẢN PRO
          </div>
        </div>
        <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
          <tr>
            <td style="padding:10px;background:#f7fafc;border-radius:8px;color:#4a5568;font-size:14px;">✅ SOS không giới hạn</td>
          </tr>
          <tr><td style="height:6px"></td></tr>
          <tr>
            <td style="padding:10px;background:#f7fafc;border-radius:8px;color:#4a5568;font-size:14px;">✅ Chạy nền bảo vệ 24/7</td>
          </tr>
          <tr><td style="height:6px"></td></tr>
          <tr>
            <td style="padding:10px;background:#f7fafc;border-radius:8px;color:#4a5568;font-size:14px;">✅ Danh bạ không giới hạn</td>
          </tr>
        </table>
        <p style="color:#718096;font-size:13px;text-align:center;">
          Gói Pro có hiệu lực đến hết ngày <strong>{expires_str}</strong>.<br>
          Sau ngày này, tài khoản sẽ tự động chuyển về gói Free.
        </p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#a0aec0;font-size:12px;text-align:center;">
          © 2024 SAFE GUARD – FPT University Cần Thơ
        </p>
      </div>
    </div>"""
    return _send(to_email, '[SAFE GUARD] Tài khoản của bạn đã được nâng cấp lên Pro ⭐', html)


def send_pro_expired(to_email: str, full_name: str) -> tuple[bool, str]:
    """Gửi email thông báo tài khoản Pro đã hết hạn."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#f4f7fb;padding:32px 16px;">
      <div style="background:#03045E;border-radius:16px 16px 0 0;padding:28px 32px;text-align:center;">
        <h1 style="color:#fff;font-size:24px;margin:0;letter-spacing:3px;">SAFE GUARD</h1>
        <p style="color:#90E0EF;margin:8px 0 0;font-size:14px;">Thông báo hết hạn gói Pro</p>
      </div>
      <div style="background:#fff;border-radius:0 0 16px 16px;padding:36px 32px;">
        <p style="color:#2d3748;font-size:15px;">Xin chào <strong>{full_name}</strong>,</p>
        <p style="color:#4a5568;font-size:14px;line-height:1.6;">
          Gói <strong>Pro</strong> của bạn đã hết hạn. Tài khoản đã được chuyển về gói <strong>Free</strong>.
        </p>
        <p style="color:#4a5568;font-size:14px;line-height:1.6;">
          Vui lòng liên hệ quản trị viên để gia hạn nếu cần.
        </p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#a0aec0;font-size:12px;text-align:center;">
          © 2024 SAFE GUARD – FPT University Cần Thơ
        </p>
      </div>
    </div>"""
    return _send(to_email, '[SAFE GUARD] Gói Pro của bạn đã hết hạn', html)


def send_reset_password_otp(to_email: str, full_name: str, otp: str) -> tuple[bool, str]:
    """Gửi OTP đặt lại mật khẩu."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#f4f7fb;padding:32px 16px;">
      <div style="background:#03045E;border-radius:16px 16px 0 0;padding:28px 32px;text-align:center;">
        <h1 style="color:#fff;font-size:24px;margin:0;letter-spacing:3px;">SAFE GUARD</h1>
        <p style="color:#90E0EF;margin:8px 0 0;font-size:14px;">Đặt lại mật khẩu</p>
      </div>
      <div style="background:#fff;border-radius:0 0 16px 16px;padding:36px 32px;">
        <p style="color:#2d3748;font-size:15px;">Xin chào <strong>{full_name}</strong>,</p>
        <p style="color:#4a5568;font-size:14px;line-height:1.6;">
          Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản <strong>SAFE GUARD</strong> của bạn.<br>
          Nhập mã OTP bên dưới trong ứng dụng để tiếp tục.
        </p>
        <div style="text-align:center;margin:32px 0;">
          <div style="display:inline-block;background:#03045E;color:#fff;
                      font-size:36px;font-weight:bold;letter-spacing:12px;
                      padding:18px 36px;border-radius:12px;">{otp}</div>
        </div>
        <p style="color:#718096;font-size:13px;text-align:center;">
          Mã có hiệu lực trong <strong>10 phút</strong>.<br>
          Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này và mật khẩu của bạn sẽ không thay đổi.
        </p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#a0aec0;font-size:12px;text-align:center;">
          © 2024 SAFE GUARD – FPT University Cần Thơ
        </p>
      </div>
    </div>"""
    return _send(to_email, f'[SAFE GUARD] Mã đặt lại mật khẩu: {otp}', html)


def send_verification_otp(to_email: str, full_name: str, otp: str) -> tuple[bool, str]:
    return _send(to_email, f'[SAFE GUARD] Mã xác thực email: {otp}',
                 _otp_html(full_name, otp, is_resend=False))


def send_resend_otp(to_email: str, full_name: str, otp: str) -> tuple[bool, str]:
    return _send(to_email, f'[SAFE GUARD] Mã xác thực mới: {otp}',
                 _otp_html(full_name, otp, is_resend=True))
