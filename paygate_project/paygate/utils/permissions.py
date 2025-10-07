from rest_framework.permissions import BasePermission

class IsMerchantUser(BasePermission):
    """
    Allows access only to users who are merchants.
    """

    def has_permission(self, request, view):
        user = request.user
        # Check if user is authenticated and linked to a Merchant
        return bool(user and user.is_authenticated and hasattr(user, 'merchant'))
