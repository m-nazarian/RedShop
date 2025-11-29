import requests
import json
from django.conf import settings

class ZarinPalService:
    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID

    def send_request(self, amount, description, email=None, mobile=None):
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": settings.ZARINPAL_CALLBACK_URL,
            "description": description,
            "metadata": {"email": email, "mobile": mobile}
        }
        headers = {'content-type': 'application/json', 'content-length': str(len(str(data)))}

        try:
            response = requests.post(settings.ZARINPAL_REQUEST_URL, data=json.dumps(data), headers=headers, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['data']['code'] == 100:
                    return {
                        'status': True,
                        'url': f"{settings.ZARINPAL_START_PAY_URL}{response_data['data']['authority']}",
                        'authority': response_data['data']['authority']
                    }
                return {'status': False, 'code': response_data['data']['code']}
            return {'status': False, 'code': 'connection_error'}
        except requests.exceptions.RequestException:
            return {'status': False, 'code': 'connection_error'}

    def verify_payment(self, authority, amount):
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority
        }
        headers = {'content-type': 'application/json', 'content-length': str(len(str(data)))}

        try:
            response = requests.post(settings.ZARINPAL_VERIFY_URL, data=json.dumps(data), headers=headers, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['data']['code'] == 100:
                    return {'status': True, 'ref_id': response_data['data']['ref_id'], 'code': 100}
                elif response_data['data']['code'] == 101:
                    return {'status': True, 'ref_id': response_data['data']['ref_id'], 'code': 101}
                return {'status': False, 'code': response_data['data']['code']}
            return {'status': False, 'code': 'connection_error'}
        except requests.exceptions.RequestException:
            return {'status': False, 'code': 'connection_error'}