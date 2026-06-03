from django.db import models

class PortfolioProfile(models.Model):
    name = models.CharField(max_length=50, verbose_name="이름")
    title = models.CharField(max_length=200, verbose_name="한 줄 소개", default="보안을 고려한 창의적인 개발자")
    skills = models.CharField(max_length=500, verbose_name="기술 스택 (쉼표로 구분)", default="Django, Python, HTMX, Alpine.js, CSS")
    profile_image = models.ImageField(upload_to='portfolio/profile/', blank=True, null=True, verbose_name="프로필 이미지")

    class Meta:
        verbose_name = "포트폴리오 프로필"
        verbose_name_plural = "포트폴리오 프로필"

    def __str__(self):
        return f"{self.name}의 프로필"

    @property
    def skill_list(self):
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        return []


SECTION_CHOICES = [
    ('education', '교육수료/학력'),
    ('experience', '경력/프로젝트'),
    ('award', '수상/대회'),
    ('certificate', '자격증'),
    ('thesis', '논문/연구'),
]

class PortfolioItem(models.Model):
    section_type = models.CharField(max_length=20, choices=SECTION_CHOICES, verbose_name="섹션 종류")
    title = models.CharField(max_length=200, verbose_name="제목 (예: 학교명, 회사명, 대회명)")
    sub_title = models.CharField(max_length=200, blank=True, verbose_name="부제목/기간/소속")
    description = models.TextField(blank=True, verbose_name="상세 설명")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")

    class Meta:
        verbose_name = "포트폴리오 항목"
        verbose_name_plural = "포트폴리오 항목 목록"
        ordering = ['order', 'id']

    def __str__(self):
        return f"[{self.get_section_type_display()}] {self.title}"
