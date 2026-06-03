from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomUserProfileForm

User = get_user_model()

@require_GET
def validate_email(request):
    email = request.GET.get('email', '').strip().lower()
    if not email:
        return HttpResponse('')
    
    # 간단한 정규식 체크나 기본 validation을 패스한 뒤 DB 중복 체크
    if User.objects.filter(email=email).exists():
        return HttpResponse('<span class="form-error-msg">❌ 이미 사용 중인 이메일입니다.</span>')
    return HttpResponse('<span class="form-success-msg">👍 사용 가능한 이메일입니다.</span>')

@require_GET
def validate_nickname(request):
    nickname = request.GET.get('nickname', '').strip()
    if not nickname:
        return HttpResponse('')
    
    if User.objects.filter(nickname=nickname).exists():
        return HttpResponse('<span class="form-error-msg">❌ 이미 사용 중인 닉네임입니다.</span>')
    return HttpResponse('<span class="form-success-msg">👍 사용 가능한 닉네임입니다.</span>')


class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        
        # HTMX 요청일 경우, 헤더를 통해 강제 리다이렉트 처리
        if self.request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = '/'
            return response
        return redirect('home')

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            # HTMX 비동기 폼 검증 에러 발생 시, 부분 조각을 반환하여 에러 표시
            # status는 422 Unprocessable Entity로 설정하여 shake 애니메이션 트리거 유도
            return render(self.request, 'accounts/partials/register_form.html', {'form': form}, status=422)
        return super().form_invalid(form)


class LoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)

        if user is not None:
            login(self.request, user)
            if self.request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = '/'
                return response
            return redirect('home')
        else:
            form.add_error(None, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'accounts/partials/login_form.html', {'form': form}, status=422)
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')


class ProfileView(LoginRequiredMixin, FormView):
    template_name = 'accounts/profile.html'
    form_class = CustomUserProfileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # 비밀번호가 변경되었을 수 있으므로 강제 세션 갱신을 우회하기 위해 재인증 처리할 수도 있지만,
        # 세션 끊김을 방지하려면 django.contrib.auth.update_session_auth_hash를 쓰거나, 다시 로그인시킵니다.
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(self.request, self.request.user)

        if self.request.headers.get('HX-Request'):
            # HTMX로 수정 완료를 보내는 경우, 성공 메시지가 담긴 폼 조각을 렌더링하고
            # 클라이언트에 성공 토스트 팝업을 띄울 수 있는 이벤트를 실어 보냅니다.
            response = render(self.request, 'accounts/partials/profile_form.html', {
                'form': self.get_form(),
                'success_message': '개인정보가 성공적으로 수정되었습니다.'
            })
            response['HX-Trigger'] = 'profileUpdated'
            return response
        
        return redirect('home')

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'accounts/partials/profile_form.html', {'form': form}, status=422)
        return super().form_invalid(form)
