import os
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.urls import reverse

import markdown
import bleach

from .models import Post, Series, Comment, CommentReaction, REACTION_CHOICES
from .forms import PostForm

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.filter(is_published=True)

        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) |
                Q(summary__icontains=query)
            )

        series_slug = self.request.GET.get('series', '').strip()
        if series_slug:
            queryset = queryset.filter(series__slug=series_slug)

        return queryset.distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['series_list'] = Series.objects.all()
        context['active_series'] = self.request.GET.get('series', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
        
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
            context = self.get_context_data()
            return render(request, 'blog/partials/post_list_partial.html', context)
        return super().get(request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return Post.objects.all()
        return Post.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # 1. Secure Markdown Rendering
        md = markdown.Markdown(extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br'
        ])
        html_content = md.convert(post.content)
        
        # 2. XSS Clean (Bleach)
        allowed_tags = bleach.ALLOWED_TAGS | {
            'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 
            'span', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'ul', 'ol', 'li', 'strong', 'em', 'blockquote'
        }
        allowed_attrs = bleach.ALLOWED_ATTRIBUTES | {
            'code': ['class'],
            'span': ['class'],
            'img': ['src', 'alt', 'title', 'class', 'style'],
            'h1': ['id'], 'h2': ['id'], 'h3': ['id'], 'h4': ['id'],
        }
        cleaned_html = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)
        
        context['rendered_content'] = cleaned_html
        context['toc'] = md.toc
        
        # 3. Retrieve comment hierarchy
        # Only top level parents, prefetch related replies and author
        comments = post.comments.filter(parent=None).prefetch_related('replies', 'author', 'reactions', 'replies__author', 'replies__reactions')
        context['root_comments'] = comments
        
        # Emoji reaction choices
        context['emoji_choices'] = REACTION_CHOICES

        # Check if current user liked this post
        context['user_liked'] = self.request.user in post.likes.all() if self.request.user.is_authenticated else False
        
        # Get adjacent posts in the same series
        if post.series:
            series_posts = post.series.posts.filter(is_published=True).order_by('created_at')
            post_list = list(series_posts)
            try:
                idx = post_list.index(post)
                context['prev_post'] = post_list[idx - 1] if idx > 0 else None
                context['next_post'] = post_list[idx + 1] if idx < len(post_list) - 1 else None
            except ValueError:
                context['prev_post'] = None
                context['next_post'] = None
        
        return context


class PostCreateView(SuperuserRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        title_slug = slugify(form.cleaned_data['title'], allow_unicode=True)
        unique_slug = title_slug
        num = 1
        while Post.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{title_slug}-{num}"
            num += 1
        form.instance.slug = unique_slug
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:index')


class PostUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        if 'title' in form.changed_data:
            title_slug = slugify(form.cleaned_data['title'], allow_unicode=True)
            unique_slug = title_slug
            num = 1
            while Post.objects.filter(slug=unique_slug).exclude(pk=self.object.pk).exists():
                unique_slug = f"{title_slug}-{num}"
                num += 1
            form.instance.slug = unique_slug
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:index')


class UploadBlogImageView(SuperuserRequiredMixin, View):
    def post(self, request):
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                return JsonResponse({'error': '허용되지 않는 파일 형식입니다.'}, status=400)
            if image_file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': '이미지 크기는 최대 10MB까지 가능합니다.'}, status=400)
                
            filename = f"blog_{uuid.uuid4().hex}{ext}"
            filepath = os.path.join('blog/images', filename)
            saved_path = default_storage.save(filepath, image_file)
            file_url = default_storage.url(saved_path)
            
            return JsonResponse({'url': file_url})
        return JsonResponse({'error': '업로드할 이미지가 없습니다.'}, status=400)


# ==========================================
# Sprint 6: Likes, Comments, Reactions Views
# ==========================================

class TogglePostLikeView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            # HTMX 비로그인 대응: 브라우저에 로그인 유도 알림 팝업 트리거
            response = HttpResponse('<span style="color:#ff4757; font-weight:700;">로그인 필요</span>')
            response['HX-Trigger'] = 'requireLogin'
            return response

        post = get_object_or_404(Post, pk=pk)
        user_liked = False
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
            user_liked = True
            
        likes_count = post.likes_count

        if request.headers.get('HX-Request'):
            # Return updated heart button fragment with animations
            return render(request, 'blog/partials/like_button.html', {
                'post': post,
                'user_liked': user_liked,
                'likes_count': likes_count
            })
        return redirect('blog:detail', slug=post.slug)


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id', None)

        if not content:
            return HttpResponse('<span class="form-error-msg">⚠️ 내용을 입력해 주세요.</span>', status=400)

        # Secure bleach clean for basic text safety
        cleaned_content = bleach.clean(content)

        parent_comment = None
        if parent_id:
            parent_comment = get_object_or_404(Comment, pk=parent_id)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=cleaned_content,
            parent=parent_comment
        )

        if request.headers.get('HX-Request'):
            # HTMX: If it's a sub-comment/reply, render a sub-row, else render root row
            if parent_comment:
                return render(request, 'blog/partials/comment_reply_row.html', {
                    'reply': comment,
                    'post': post,
                    'emoji_choices': REACTION_CHOICES
                })
            else:
                return render(request, 'blog/partials/comment_root_row.html', {
                    'comment': comment,
                    'post': post,
                    'emoji_choices': REACTION_CHOICES
                })
        return redirect('blog:detail', slug=post.slug)


class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)

        # Authority Check (Secure coding: author or superuser only)
        if comment.author != request.user and not request.user.is_superuser:
            return HttpResponseForbidden("권한이 없습니다.")

        # Soft delete comment
        comment.is_deleted = True
        comment.save()

        if request.headers.get('HX-Request'):
            # Return updated soft-deleted fragment
            return HttpResponse('<span style="color: var(--color-text-muted); font-style: italic; font-size: 0.95rem;">🚫 삭제된 댓글입니다.</span>')
        return redirect('blog:detail', slug=comment.post.slug)


class ToggleCommentReactionView(LoginRequiredMixin, View):
    def post(self, request, pk, reaction_type):
        comment = get_object_or_404(Comment, pk=pk)
        
        # Toggle reaction logic
        existing_reaction = CommentReaction.objects.filter(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )
        
        if existing_reaction.exists():
            existing_reaction.delete()
        else:
            CommentReaction.objects.create(
                comment=comment,
                user=request.user,
                reaction_type=reaction_type
            )

        if request.headers.get('HX-Request'):
            # Count reactions group by type and return partial
            # Aggregation logic
            reactions_summary = comment.reactions.values('reaction_type').annotate(count=Count('id'))
            
            # Map values for rendering
            reactions_dict = {key: 0 for key, _ in REACTION_CHOICES}
            for r in reactions_summary:
                reactions_dict[r['reaction_type']] = r['count']
                
            # Check user reacted
            user_reactions = list(comment.reactions.filter(user=request.user).values_list('reaction_type', flat=True))

            return render(request, 'blog/partials/comment_reactions_bar.html', {
                'comment': comment,
                'reactions_dict': reactions_dict,
                'user_reactions': user_reactions,
                'emoji_choices': REACTION_CHOICES
            })
        return redirect('blog:detail', slug=comment.post.slug)
