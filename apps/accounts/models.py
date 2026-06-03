from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, nickname, name, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수 입력 항목입니다.')
        if not nickname:
            raise ValueError('닉네임은 필수 입력 항목입니다.')
        if not name:
            raise ValueError('이름은 필수 입력 항목입니다.')
            
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nickname=nickname,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, nickname, name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='이메일')
    nickname = models.CharField(max_length=50, unique=True, verbose_name='닉네임')
    name = models.CharField(max_length=50, verbose_name='이름')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name='프로필 이미지')
    
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부')
    is_staff = models.BooleanField(default=False, verbose_name='스태프 여부')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='가입일')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname', 'name']

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return f"{self.nickname} ({self.email})"
