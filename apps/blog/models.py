from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Series(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="시리즈명")
    slug = models.SlugField(max_length=150, unique=True, allow_unicode=True, verbose_name="슬러그")
    description = models.TextField(blank=True, verbose_name="시리즈 설명")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "시리즈"
        verbose_name_plural = "시리즈 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # allow_unicode=True로 한글 슬러그 자동 생성 지원
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="작성자")
    title = models.CharField(max_length=200, verbose_name="제목")
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True, verbose_name="슬러그")
    content = models.TextField(verbose_name="본문 내용")
    summary = models.TextField(blank=True, verbose_name="요약글(설명)")
    series = models.ForeignKey(Series, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts", verbose_name="시리즈")
    is_published = models.BooleanField(default=False, verbose_name="공개 여부")
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="liked_posts", verbose_name="좋아요 누른 사용자 목록")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "블로그 게시글"
        verbose_name_plural = "블로그 게시글 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            
        # 기존 요약글이 없거나 본문이 존재할 시, 수동 입력된 요약글도 마크다운을 걷어내기 위해 정제 대상으로 선정
        target_text = self.summary.strip() if self.summary else ""
        if not target_text and self.content:
            target_text = self.content
            
        if target_text:
            import re
            # 1. 마크다운 이미지 치환 (![alt](url) -> [사진])
            cleaned = re.sub(r'!\[.*?\]\(.*?\)', '[사진]', target_text)
            # 2. 마크다운 링크 치환 ([text](url) -> text)
            cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)
            # 3. 마크다운 강조 치환 (**text** or *text* -> text)
            cleaned = re.sub(r'[\*_]{1,3}(.*?)[\*_]{1,3}', r'\1', cleaned)
            # 4. 제목 헤더 기호 (#) 제거
            cleaned = re.sub(r'#+', '', cleaned)
            # 5. 개행을 공백으로 단일화하고 앞뒤 공백 제거
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            # 6. 첫 150자를 요약글로 설정
            self.summary = cleaned[:150]
        else:
            self.summary = ""
            
        super().save(*args, **kwargs)

    @property
    def likes_count(self):
        return self.likes.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="게시글")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="댓글 작성자")
    content = models.TextField(verbose_name="댓글 내용")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies", verbose_name="부모 댓글")
    is_deleted = models.BooleanField(default=False, verbose_name="삭제 여부 (소프트 삭제)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    class Meta:
        verbose_name = "댓글"
        verbose_name_plural = "댓글 목록"
        ordering = ['created_at']

    def __str__(self):
        if self.is_deleted:
            return f"[삭제된 댓글] {self.pk}"
        return f"{self.author.nickname}: {self.content[:30]}"

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def like_count(self):
        return self.reactions.filter(reaction_type='like').count()

    @property
    def love_count(self):
        return self.reactions.filter(reaction_type='love').count()

    @property
    def haha_count(self):
        return self.reactions.filter(reaction_type='haha').count()

    @property
    def wow_count(self):
        return self.reactions.filter(reaction_type='wow').count()

    @property
    def sad_count(self):
        return self.reactions.filter(reaction_type='sad').count()

    @property
    def angry_count(self):
        return self.reactions.filter(reaction_type='angry').count()


REACTION_CHOICES = [
    ('like', '👍 좋아요'),
    ('love', '❤️ 하트'),
    ('haha', '😂 웃겨요'),
    ('wow', '😮 놀라워요'),
    ('sad', '😥 슬퍼요'),
    ('angry', '😡 화나요'),
]

class CommentReaction(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=15, choices=REACTION_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['comment', 'user', 'reaction_type'], name='unique_comment_reaction')
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.reaction_type} on Comment {self.comment.id}"
