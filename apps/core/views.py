from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden

from blog.models import Post, Series, Comment

User = get_user_model()

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser


class HomeView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch actual latest 3 published posts from DB
        context['recent_posts'] = Post.objects.filter(is_published=True).order_by('-created_at')[:3]
        return context


# ==========================================
# Sprint 7: Custom Admin Dashboard views
# ==========================================

class AdminDashboardView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate brief statistics
        context['total_users'] = User.objects.count()
        context['total_posts'] = Post.objects.count()
        context['total_comments'] = Comment.objects.count()
        
        # Load object lists
        context['users_list'] = User.objects.all().order_by('-date_joined')
        context['posts_list'] = Post.objects.all().order_by('-created_at')
        context['series_list'] = Series.objects.all().order_by('-created_at')
        
        return context


class AdminUserToggleActiveView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        # Prevent self-deactivation
        if user == request.user:
            return HttpResponse('<span style="color:#ff4757; font-weight:700;">본인 계정 비활성화 불가</span>', status=400)
            
        user.is_active = not user.is_active
        user.save()
        
        if request.headers.get('HX-Request'):
            # Return updated active toggle status badge
            if user.is_active:
                return HttpResponse('<span class="badge-status-active" style="background-color:rgba(46, 213, 115, 0.12); color:#2ed573; padding:0.3rem 0.7rem; border-radius:8px; font-weight:700;">활성화</span>')
            else:
                return HttpResponse('<span class="badge-status-inactive" style="background-color:rgba(255, 71, 87, 0.12); color:#ff4757; padding:0.3rem 0.7rem; border-radius:8px; font-weight:700;">비활성화</span>')
        return redirect('core:admin_dashboard')


class AdminPostTogglePublishView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.is_published = not post.is_published
        post.save()
        
        if request.headers.get('HX-Request'):
            # Return updated publish toggle status badge
            if post.is_published:
                return HttpResponse('<span class="badge-status-active" style="background-color:rgba(46, 213, 115, 0.12); color:#2ed573; padding:0.3rem 0.7rem; border-radius:8px; font-weight:700;">공개</span>')
            else:
                return HttpResponse('<span class="badge-status-inactive" style="background-color:rgba(255, 71, 87, 0.12); color:#ff4757; padding:0.3rem 0.7rem; border-radius:8px; font-weight:700;">🔒 비공개</span>')
        return redirect('core:admin_dashboard')


class AdminSeriesDeleteView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        series = get_object_or_404(Series, pk=pk)
        series.delete()
        
        # HTMX row delete swap
        return HttpResponse('')


# ==========================================
# Premium Error Custom Views
# ==========================================

def error_403_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500_view(request):
    return render(request, 'errors/500.html', status=500)
