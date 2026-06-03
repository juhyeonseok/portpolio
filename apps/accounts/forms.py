from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요',
            'class': 'form-input'
        }),
        min_length=8,
        error_messages={'min_length': '비밀번호는 최소 8자 이상이어야 합니다.'}
    )
    password_confirm = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 다시 입력하세요',
            'class': 'form-input'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'nickname', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': '이메일 주소를 입력하세요',
                'class': 'form-input',
                'hx-get': '/accounts/validate-email/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#email-error',
                'hx-sync': 'this:replace'
            }),
            'nickname': forms.TextInput(attrs={
                'placeholder': '사용할 닉네임을 입력하세요',
                'class': 'form-input',
                'hx-get': '/accounts/validate-nickname/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#nickname-error',
                'hx-sync': 'this:replace'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': '실명을 입력하세요',
                'class': 'form-input'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('이미 등록된 이메일 주소입니다.')
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname').strip()
        if User.objects.filter(nickname=nickname).exists():
            raise ValidationError('이미 사용 중인 닉네임입니다.')
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', '비밀번호가 일치하지 않습니다.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(forms.Form):
    username = forms.EmailField(
        label='이메일',
        widget=forms.EmailInput(attrs={
            'placeholder': '이메일을 입력하세요',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요',
            'class': 'form-input'
        })
    )


class CustomUserProfileForm(forms.ModelForm):
    current_password = forms.CharField(
        label='현재 비밀번호 확인',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': '현재 비밀번호를 입력하세요',
            'class': 'form-input'
        })
    )
    new_password = forms.CharField(
        label='새 비밀번호 (변경할 경우에만 입력)',
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': '변경할 경우에만 8자 이상 입력',
            'class': 'form-input'
        }),
        min_length=8,
        error_messages={'min_length': '비밀번호는 최소 8자 이상이어야 합니다.'}
    )
    new_password_confirm = forms.CharField(
        label='새 비밀번호 확인',
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': '새 비밀번호를 다시 입력하세요',
            'class': 'form-input'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'nickname', 'name', 'profile_image']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'nickname': forms.TextInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('현재 비밀번호가 일치하지 않습니다.')
        return current_password

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('이미 다른 회원이 사용 중인 이메일입니다.')
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname').strip()
        if User.objects.filter(nickname=nickname).exclude(pk=self.user.pk).exists():
            raise ValidationError('이미 다른 회원이 사용 중인 닉네임입니다.')
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password or new_password_confirm:
            if new_password != new_password_confirm:
                self.add_error('new_password_confirm', '새 비밀번호가 일치하지 않습니다.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user
