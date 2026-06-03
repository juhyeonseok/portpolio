import json
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import PortfolioProfile, PortfolioItem, SECTION_CHOICES

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser


class PortfolioView(TemplateView):
    template_name = 'portfolio/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create default profile
        profile, created = PortfolioProfile.objects.get_or_create(
            id=1,
            defaults={
                'name': '주현석',
                'title': '보안을 깊이 이해하고 창의적으로 개발하는 시니어 DevSecOps 엔지니어',
                'skills': 'Django, Python, HTMX, Alpine.js, Vanilla CSS, Docker, Secure Coding'
            }
        )
        context['profile'] = profile
        
        # Categorize items
        items = PortfolioItem.objects.all().order_by('order', 'id')
        context['education_items'] = items.filter(section_type='education')
        context['experience_items'] = items.filter(section_type='experience')
        context['award_items'] = items.filter(section_type='award')
        context['certificate_items'] = items.filter(section_type='certificate')
        context['thesis_items'] = items.filter(section_type='thesis')
        
        return context


class PortfolioEditView(SuperuserRequiredMixin, TemplateView):
    template_name = 'portfolio/edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(PortfolioProfile, id=1)
        context['sections'] = SECTION_CHOICES
        context['items'] = PortfolioItem.objects.all().order_by('section_type', 'order', 'id')
        return context


class UpdateProfileInfoView(SuperuserRequiredMixin, View):
    def post(self, request):
        profile = get_object_or_404(PortfolioProfile, id=1)
        profile.name = request.POST.get('name', '').strip()
        profile.title = request.POST.get('title', '').strip()
        profile.skills = request.POST.get('skills', '').strip()
        profile.save()
        
        if request.headers.get('HX-Request'):
            # Return updated dynamic segment or full success signal
            return HttpResponse('<div class="form-global-success animate-fade-in-up" style="background-color: rgba(46, 213, 115, 0.08); border: 1px solid rgba(46, 213, 115, 0.2); padding: 0.8rem 1.2rem; border-radius: 12px; color: #2ed573; font-weight:600;">✅ 프로필 메타 정보가 저장되었습니다.</div>')
        return HttpResponse('Success')


class UploadProfileImageView(SuperuserRequiredMixin, View):
    def post(self, request):
        profile = get_object_or_404(PortfolioProfile, id=1)
        
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
            profile.save()
            
            # 드래그앤드롭 업로드 후 갱신된 이미지 태그를 리턴하거나 JSON 반환
            image_url = profile.profile_image.url
            if request.headers.get('HX-Request'):
                return HttpResponse(f'<img src="{image_url}" class="profile-avatar animate-scale-in" alt="프로필 사진">')
            return JsonResponse({'status': 'success', 'image_url': image_url})
            
        return HttpResponse('No image uploaded', status=400)


class AddPortfolioItemView(SuperuserRequiredMixin, View):
    def post(self, request):
        section_type = request.POST.get('section_type', '').strip()
        title = request.POST.get('title', '').strip()
        sub_title = request.POST.get('sub_title', '').strip()
        description = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)
        
        try:
            order = int(order)
        except ValueError:
            order = 0

        if not section_type or not title:
            return HttpResponse('<span class="form-error-msg">⚠️ 섹션 종류와 제목은 필수입니다.</span>', status=400)

        item = PortfolioItem.objects.create(
            section_type=section_type,
            title=title,
            sub_title=sub_title,
            description=description,
            order=order
        )

        if request.headers.get('HX-Request'):
            # 리스트에 즉시 삽입될 HTML 조각을 리턴
            return render(request, 'portfolio/partials/portfolio_item_row.html', {'item': item})
        return HttpResponse('Success')


class DeletePortfolioItemView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(PortfolioItem, pk=pk)
        item.delete()
        
        # HTMX hx-swap="delete"에 부합하도록 아무 내용도 반환하지 않음
        return HttpResponse('')
