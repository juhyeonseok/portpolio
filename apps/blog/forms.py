from django import forms
from .models import Post, Series

class PostForm(forms.ModelForm):
    # 신규 시리즈 생성을 위한 간편 필드 추가
    new_series_name = forms.CharField(
        label='새 시리즈 생성 (필요한 경우에만 입력)',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '새로 생성할 시리즈 이름을 입력하세요',
            'class': 'form-input'
        })
    )

    class Meta:
        model = Post
        fields = ['title', 'series', 'content', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': '게시글 제목을 입력하세요',
                'class': 'form-input',
                'style': 'font-size: 1.3rem; font-weight: 700;'
            }),
            'series': forms.Select(attrs={
                'class': 'form-input',
                'style': 'appearance: auto;'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': '여기에 마크다운 문법으로 본문을 입력하세요. 이미지 복사(Ctrl+V) 및 파일 드래그앤드롭 업로드를 지원합니다.',
                'class': 'form-input editor-textarea',
                'rows': 25,
                'style': 'font-family: monospace; line-height: 1.5; font-size: 0.95rem; resize: none;'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-checkbox-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['series'].empty_label = "-- 시리즈 선택 안 함 --"

    def save(self, commit=True):
        post = super().save(commit=False)
        new_series_name = self.cleaned_data.get('new_series_name', '').strip()
        
        if new_series_name:
            # 새 시리즈 생성 또는 기존 시리즈와 매칭
            series, created = Series.objects.get_or_create(
                name=new_series_name
            )
            post.series = series
            
        if commit:
            post.save()
        return post
