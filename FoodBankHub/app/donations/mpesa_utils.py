import requests
import base64
import json
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MPesaService:
    """
    M-Pesa Daraja API integration for STK Push payments
    """
    
    def __init__(self):
        # M-Pesa API Configuration (add these to your settings.py)
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        
        # API URLs (Sandbox - change for production)
        self.base_url = "https://sandbox.safaricom.co.ke"
        self.auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
    
    def get_access_token(self):
        """
        Get OAuth access token from M-Pesa API
        """
        try:
            # Encode credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(self.auth_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('access_token')
            
        except Exception as e:
            logger.error(f"Error getting M-Pesa access token: {e}")
            return None
    
    def generate_password(self):
        """
        Generate password for STK Push request
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push payment request
        
        Args:
            phone_number (str): Customer phone number (format: 254XXXXXXXXX)
            amount (int): Amount to be paid
            account_reference (str): Reference for the transaction
            transaction_desc (str): Description of the transaction
        
        Returns:
            dict: Response from M-Pesa API
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            password, timestamp = self.generate_password()
            
            # Format phone number (ensure it starts with 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('7'):
                phone_number = '254' + phone_number
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription'),
                    'customer_message': data.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('ResponseDescription', 'Unknown error'),
                    'response_code': data.get('ResponseCode')
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"M-Pesa API request error: {e}")
            return {'success': False, 'error': 'Network error occurred'}
        except Exception as e:
            logger.error(f"M-Pesa STK Push error: {e}")
            return {'success': False, 'error': str(e)}
    
    def query_transaction_status(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id (str): CheckoutRequestID from STK Push response
        
        Returns:
            dict: Transaction status response
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            password, timestamp = self.generate_password()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            response = requests.post(query_url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"M-Pesa query error: {e}")
            return {'success': False, 'error': str(e)}


def process_mpesa_donation(donation):
    """
    Process M-Pesa payment for a donation
    
    Args:
        donation: Donation model instance
    
    Returns:
        dict: Payment processing result
    """
    if donation.donation_type != 'money' or not donation.mpesa_phone:
        return {'success': False, 'error': 'Invalid donation for M-Pesa processing'}
    
    mpesa_service = MPesaService()
    
    # Create account reference (donation ID)
    account_reference = f"DONATION-{donation.id}"
    
    # Create transaction description
    transaction_desc = f"Donation to {donation.foodbank.foodbank_name}"
    
    # Initiate STK Push
    result = mpesa_service.initiate_stk_push(
        phone_number=donation.mpesa_phone,
        amount=donation.amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc
    )
    
    return result
