from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

class RateLimitedMixin:
    """
    Apply rate limiting to any CBV by decorating its dispatch method.
    """
    @classmethod
    def as_view(cls, **initkwargs):
        # Call the original as_view to get the view function
        view = super().as_view(**initkwargs)
        # Wrap the view function directly with ratelimit
        return ratelimit(key='ip', rate='500/m', block=True)(view)
