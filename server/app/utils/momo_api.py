import requests
import logging
from flask import current_app
import uuid
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class MobileMoneyAPI:
    """Class to handle MTN MoMo Collections API interactions."""
    
    def __init__(self):
        self.base_url = current_app.config['MOMO_BASE_URL']
        self.api_key = current_app.config['MOMO_API_KEY']
        self.api_secret = current_app.config['MOMO_API_SECRET']
        self.subscription_type = current_app.config.get('MOMO_SUBSCRIPTION_TYPE', 'collection')
        self.api_user_id = current_app.config.get('MOMO_API_USER_ID', 'your-api-user-id')  # Set in .env
        self.token = None
        self.token_expiry = None

    def get_access_token(self):
        """Obtain an access token for MTN MoMo API."""
        if self.token and self.token_expiry and self.token_expiry > datetime.utcnow():
            return self.token

        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_secret,
                'Content-Type': 'application/json'
            }
            payload = {
                'grant_type': 'client_credentials'
            }
            response = requests.post(
                f'{self.base_url}/collection/token/',
                auth=(self.api_user_id, self.api_key),
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.token = data['access_token']
            self.token_expiry = datetime.utcnow() + timedelta(seconds=data['expires_in'] - 300)  # Buffer
            logger.info("MTN MoMo access token obtained")
            return self.token
        except requests.RequestException as e:
            logger.error(f"Failed to obtain MTN MoMo access token: {str(e)}")
            raise

    def initiate_payment(self, phone_number: str, amount: float, package_id: str) -> dict:
        """
        Initiate a mobile money payment using MTN MoMo Collections API.
        Args:
            phone_number: User's phone number (e.g., +1234567890).
            amount: Payment amount in local currency.
            package_id: ID of the selected internet package.
        Returns:
            Dict with transaction ID and status, or error message.
        """
        try:
            transaction_id = str(uuid.uuid4())
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Reference-Id': transaction_id,
                'X-Target-Environment': 'sandbox',
                'Ocp-Apim-Subscription-Key': self.api_secret,
                'Content-Type': 'application/json'
            }
            payload = {
                'amount': str(amount),
                'currency': 'EUR',  # MTN MoMo sandbox uses EUR
                'externalId': transaction_id,
                'payer': {
                    'partyIdType': 'MSISDN',
                    'partyId': phone_number.lstrip('+')
                },
                'payerMessage': f'Internet package {package_id} purchase',
                'payeeNote': 'Internet Portal Payment'
            }

            response = requests.post(
                f'{self.base_url}/collection/v1_0/requesttopay',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Payment initiated: transaction_id={transaction_id}, phone={phone_number}")
            return {
                'transaction_id': transaction_id,
                'status': 'PENDING',
                'message': 'Payment initiated'
            }
        except requests.RequestException as e:
            logger.error(f"Payment initiation failed: phone={phone_number}, error={str(e)}")
            return {'error': 'Payment initiation failed', 'details': str(e)}

    def verify_payment(self, transaction_id: str) -> dict:
        """
        Verify the status of a payment transaction.
        
        Args:
            transaction_id: Unique transaction ID from the payment provider.
            
        Returns:
            Dict with:
            - Standardized status ('SUCCESSFUL', 'PENDING', 'FAILED', 'UNKNOWN')
            - Transaction details
            - Error info if verification failed
        """
        try:
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Target-Environment': 'sandbox',
                'Ocp-Apim-Subscription-Key': self.api_secret
            }
            
            response = requests.get(
                f'{self.base_url}/collection/v1_0/requesttopay/{transaction_id}',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Standardize status values
            raw_status = data.get('status', '').upper()
            status = 'SUCCESSFUL' if raw_status == 'SUCCESS' else raw_status
            
            logger.info(f"Payment verified: transaction_id={transaction_id}, status={status}")
            
            return {
                'transaction_id': transaction_id,
                'status': status,  # Standardized status
                'amount': float(data.get('amount', 0)),
                'currency': data.get('currency', ''),
                'phone_number': '+' + data.get('payer', {}).get('partyId', ''),
                'timestamp': data.get('createdAt', '')
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Payment verification HTTP error: {transaction_id}, status={e.response.status_code}")
            return {
                'error': 'PAYMENT_VERIFICATION_FAILED',
                'status': 'FAILED',
                'http_status': e.response.status_code,
                'details': str(e)
            }
            
        except Exception as e:
            logger.error(f"Payment verification failed: {transaction_id}, error={str(e)}")
            return {
                'error': 'VERIFICATION_SYSTEM_ERROR',
                'status': 'UNKNOWN',
                'details': str(e)
            }

    def refund_payment(self, transaction_id: str, amount: float) -> dict:
        """
        Initiate a refund for a failed or canceled transaction.
        Args:
            transaction_id: Unique transaction ID.
            amount: Amount to refund.
        Returns:
            Dict with refund status or error message.
        """
        try:
            token = self.get_access_token()
            refund_id = str(uuid.uuid4())
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Reference-Id': refund_id,
                'X-Target-Environment': 'sandbox',
                'Ocp-Apim-Subscription-Key': self.api_secret,
                'Content-Type': 'application/json'
            }
            payload = {
                'amount': str(amount),
                'currency': 'EUR',
                'externalId': refund_id,
                'referenceIdToRefund': transaction_id,
                'payerMessage': 'Refund for failed transaction',
                'payeeNote': 'Internet Portal Refund'
            }

            response = requests.post(
                f'{self.base_url}/collection/v1_0/refund',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Refund processed: transaction_id={transaction_id}, amount={amount}")
            return {
                'transaction_id': transaction_id,
                'status': 'REFUNDED',
                'message': 'Refund processed'
            }
        except requests.RequestException as e:
            logger.error(f"Refund failed: transaction_id={transaction_id}, error={str(e)}")
            return {'error': 'Refund failed', 'details': str(e)}
