# utils/helpers.py
from ..models import Merchant
from ..jsonResponse.response import JSONResponseSender

def get_merchant_from_user(user):
    try:
        return Merchant.objects.get(user=user)
    except Merchant.DoesNotExist:
        return None
