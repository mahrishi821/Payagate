from django.http import JsonResponse


class JSONResponseSender:
    @staticmethod
    def send_success(data=None, message='Success', status=200):
        payload = {'success': True, 'message': message, 'data': data}
        return JsonResponse(payload, status=status)

    @staticmethod
    def send_error(code=101, message='Error', description='Description', meta=None, status=200):
        exception = {
            'code': code,
            'message': message,
            'description': description,
            'meta': meta
        }
        payload = {'success': False, 'exception': exception}
        return JsonResponse(payload, status=status)