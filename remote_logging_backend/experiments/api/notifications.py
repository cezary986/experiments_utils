import requests
from django.conf import settings


def send_notification(title: str, message: str):
    print('SEND')
    headers = {
        'Authorization': f'key={settings.FIREBASE_API_KEY}',
        'Content-type': 'application/json'

    }
    requests.post(
        url='https://fcm.googleapis.com/fcm/send',
        headers=headers,
        json={
            "notification": {
                'title': title,
                'body': message,
            },
            "to": settings.NOTIFICATIONS_TOKEN
        }
    )
