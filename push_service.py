"""
Firebase Cloud Messaging (FCM) push notification service.
Cần set Railway variable:
  FIREBASE_SERVER_KEY = <Firebase Cloud Messaging server key>
  (Firebase console → Project Settings → Cloud Messaging → Server key)
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

FCM_URL = 'https://fcm.googleapis.com/fcm/send'


def _server_key() -> str:
    return os.environ.get('FIREBASE_SERVER_KEY', '')


def send_push(tokens: list, title: str, body: str, data: dict = None) -> bool:
    """Send push notification to a list of FCM tokens. Returns True if at least one succeeded."""
    key = _server_key()
    if not key:
        logger.warning('Push not sent: FIREBASE_SERVER_KEY not configured')
        return False
    if not tokens:
        return False

    payload = {
        'registration_ids': tokens,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default',
            'android_channel_id': 'safe_guard_sos',
        },
        'data': data or {},
        'priority': 'high',
        'android': {
            'priority': 'HIGH',
            'notification': {
                'channel_id': 'safe_guard_sos',
                'default_sound': True,
                'default_vibrate_timings': True,
            }
        }
    }
    try:
        resp = requests.post(
            FCM_URL,
            json=payload,
            headers={
                'Authorization': f'key={key}',
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
        result = resp.json()
        success_count = result.get('success', 0)
        logger.info(f'FCM sent to {len(tokens)} tokens, success={success_count}')
        return success_count > 0
    except Exception as e:
        logger.error(f'FCM error: {e}')
        return False


def notify_sos(admin_tokens: list, sender_name: str, location: str, message: str = '') -> bool:
    """Notify admins when a user sends SOS."""
    body = f'{sender_name} cần trợ giúp tại {location}'
    if message:
        body += f' — {message}'
    return send_push(
        tokens=admin_tokens,
        title='🆘 CẢNH BÁO SOS',
        body=body,
        data={'type': 'sos', 'sender': sender_name, 'location': location},
    )


def notify_account_locked(user_tokens: list) -> bool:
    """Notify user that their account was locked by admin."""
    return send_push(
        tokens=user_tokens,
        title='⚠️ Tài khoản bị khóa',
        body='Tài khoản của bạn đã bị admin khóa. Liên hệ hỗ trợ để biết thêm.',
        data={'type': 'account_locked'},
    )


def notify_pro_activated(user_tokens: list) -> bool:
    """Notify user that their account was upgraded to Pro."""
    return send_push(
        tokens=user_tokens,
        title='⭐ Tài khoản Pro đã kích hoạt!',
        body='Bạn đã được nâng cấp lên gói Pro. Tận hưởng tất cả tính năng không giới hạn.',
        data={'type': 'pro_activated'},
    )
