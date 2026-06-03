from django.core.exceptions import PermissionDenied

class AdminAccessRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        # /admin/ 또는 /admin-panel/ 경로이면서 슈퍼유저가 아닌 유저의 접근 철저 차단 (로그인조차 미노출)
        if path.startswith('/admin/') or path.startswith('/admin-panel/'):
            if not request.user.is_authenticated or not request.user.is_superuser:
                raise PermissionDenied("이 페이지에 접근할 권한이 없습니다.")
                
        response = self.get_response(request)
        return response
