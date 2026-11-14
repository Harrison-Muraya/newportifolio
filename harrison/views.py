import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404, StreamingHttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Count

from .models import GalleryImage, ImageLike, ImageComment, ContactMessage, Project
from .portfolio_data import CASE_STUDIES, SKILL_GROUPS

PORTFOLIO_SKILLS = [
    ("PHP & Laravel", 90),
    ("Python & Django", 85),
    ("JavaScript & React", 80),
    ("MySQL & Databases", 85),
    ("Machine Learning", 75),
    ("DevOps & Linux", 78),
]


# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
def home(request):
    gallery_images = GalleryImage.objects.all()
    projects = Project.objects.all()

    return render(request, 'harrison/home.html', {
        'gallery_images': gallery_images,
        'projects': projects,
        'skills': PORTFOLIO_SKILLS,
        'case_studies': CASE_STUDIES[:3],
    })


def work(request):
    return render(request, 'harrison/work.html', {
        'case_studies': CASE_STUDIES,
    })


def work_detail(request, slug):
    for index, study in enumerate(CASE_STUDIES):
        if study['slug'] == slug:
            next_study = CASE_STUDIES[(index + 1) % len(CASE_STUDIES)]
            return render(request, 'harrison/work_detail.html', {
                'study': study,
                'next_study': next_study,
            })
    raise Http404('Case study not found.')


def lab(request):
    return render(request, 'harrison/lab.html', {
        'case_studies': CASE_STUDIES,
    })


AGENT_CHAT_URL = getattr(
    settings,
    "AGENT_CHAT_URL",
    os.environ.get(
        "AGENT_CHAT_URL",
        "https://supervisors-moral-dive-program.trycloudflare.com/chat",
    ),
)

INSTANT_FAQ = (
    (
        ("full name",),
        "Harrison Ng'ang'a Muraya.",
    ),
    (
        ("who are you", "who is harrison", "wewe ni nani"),
        "I'm Harrison Ng'ang'a Muraya — fullstack developer in Nairobi.",
    ),
    (
        ("what is your email", "what's your email", "your email"),
        "hezronmuraya9@gmail.com",
    ),
    (
        ("phone number", "your phone", "your number"),
        "+254 726 688 832",
    ),
    (
        ("how do i contact", "reach you", "contact you"),
        "Email hezronmuraya9@gmail.com, call +254 726 688 832, or LinkedIn linkedin.com/in/muraya-harrison.",
    ),
    (
        ("what have you built", "umejenga"),
        "Flagship work: HostPro, KENA Coin, Ashkey RideDelivery, Sunne, Alpha Loans, and Harrison Agent. GitHub: github.com/Harrison-Muraya.",
    ),
    (
        ("where do you work", "current job", "afripixel"),
        "Software developer at Afripixel Solution since July 2026.",
    ),
)


def instant_faq_reply(message: str) -> str | None:
    lower = message.lower().strip()
    # Follow-ups belong to the agent thread (history + canonical).
    if lower.startswith(("and ", "also ", "what about ", "how about ")):
        return None
    for keys, reply in INSTANT_FAQ:
        if any(key in lower for key in keys):
            return reply
    return None


def agent_chat(request):
    return render(request, "harrison/chat.html")


@require_POST
def agent_chat_send(request):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Send a plain text question."}, status=400)
    message = str(payload.get("message") or "").strip()
    if not message or len(message) > 4000:
        return JsonResponse({"detail": "Write a question first."}, status=400)
    instant = instant_faq_reply(message)
    if instant:
        return JsonResponse({"reply": instant, "agent": "instant"})
    history = []
    raw_history = payload.get("history") or []
    if isinstance(raw_history, list):
        for turn in raw_history[-12:]:
            if not isinstance(turn, dict):
                continue
            role = turn.get("role")
            content = str(turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                history.append({"role": role, "content": content[:4000]})
    body = json.dumps({"message": message, "history": history, "stream": False}).encode()
    req = urllib.request.Request(
        AGENT_CHAT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse({"detail": "The agent is not reachable right now."}, status=502)
    reply = str(data.get("reply") or "").strip()
    if not reply:
        return JsonResponse({"detail": "The agent returned an empty reply."}, status=502)
    return JsonResponse({"reply": reply, "agent": data.get("agent", "remote")})


@require_POST
def agent_chat_stream(request):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Send a plain text question."}, status=400)
    message = str(payload.get("message") or "").strip()
    if not message or len(message) > 4000:
        return JsonResponse({"detail": "Write a question first."}, status=400)
    instant = instant_faq_reply(message)
    if instant:
        def instant_events():
            yield f"data: {json.dumps({'agent': 'instant'})}\n\n"
            for word in instant.split(" "):
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            yield 'data: {"done": true}\n\n'
        return StreamingHttpResponse(
            instant_events(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    history = []
    raw_history = payload.get("history") or []
    if isinstance(raw_history, list):
        for turn in raw_history[-12:]:
            if not isinstance(turn, dict):
                continue
            role = turn.get("role")
            content = str(turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                history.append({"role": role, "content": content[:4000]})
    body = json.dumps({"message": message, "history": history, "stream": True}).encode()
    req = urllib.request.Request(
        AGENT_CHAT_URL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )

    def remote_events():
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    yield chunk.decode(errors="replace")
        except (urllib.error.URLError, TimeoutError):
            yield f"data: {json.dumps({'error': 'The agent is not reachable right now.'})}\n\n"

    return StreamingHttpResponse(
        remote_events(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def about(request):
    gallery_images = GalleryImage.objects.all()
    return render(request, 'harrison/about.html', {
        'gallery_images': gallery_images,
        'skills': PORTFOLIO_SKILLS,
        'skill_groups': SKILL_GROUPS,
    })


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'harrison/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not username or not password1:
            messages.error(request, 'Username and password are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username, email=email,
                password=password1, first_name=first_name, last_name=last_name,
            )
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('home')
    return render(request, 'harrison/register.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ─────────────────────────────────────────────
# SUPERUSER DASHBOARD
# ─────────────────────────────────────────────
def superuser_required(view_func):
    """Decorator: must be logged in AND superuser."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not request.user.is_superuser:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@superuser_required
def dashboard(request):
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    total_messages = ContactMessage.objects.count()
    total_projects = Project.objects.count()
    total_gallery = GalleryImage.objects.count()
    recent_messages = ContactMessage.objects.order_by('-sent_at')[:5]
    projects = Project.objects.all()

    return render(request, 'harrison/dashboard.html', {
        'unread_count': unread_count,
        'total_messages': total_messages,
        'total_projects': total_projects,
        'total_gallery': total_gallery,
        'recent_messages': recent_messages,
        'projects': projects,
    })


# ─────────────────────────────────────────────
# MESSAGES INBOX
# ─────────────────────────────────────────────
@superuser_required
def inbox(request):
    filter_type = request.GET.get('filter', 'all')
    qs = ContactMessage.objects.all()
    if filter_type == 'unread':
        qs = qs.filter(is_read=False)
    elif filter_type == 'read':
        qs = qs.filter(is_read=True)

    unread_count = ContactMessage.objects.filter(is_read=False).count()
    return render(request, 'harrison/inbox.html', {
        'messages_list': qs,
        'filter_type': filter_type,
        'unread_count': unread_count,
    })


@superuser_required
def message_detail(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    # Auto-mark as read when opened
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    return render(request, 'harrison/message_detail.html', {
        'msg': msg,
        'unread_count': unread_count,
    })


@superuser_required
@require_POST
def message_toggle_read(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    msg.is_read = not msg.is_read
    msg.save()
    return JsonResponse({'is_read': msg.is_read})


@superuser_required
@require_POST
def message_delete(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    msg.delete()
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# AGENT TRAINING INBOX (superuser only)
# ─────────────────────────────────────────────
# Proxies GET /learn/inbox and POST /learn/reward on the agent.
# Auth: X-Teach-Token from TEACH_TOKEN (server-only). Never expose to the browser.

def agent_learn_origin():
    raw = getattr(settings, "AGENT_CHAT_URL", "") or os.environ.get("AGENT_CHAT_URL", "")
    parts = urlsplit(str(raw).strip())
    if not parts.scheme or not parts.netloc:
        return ""
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def agent_teach_token():
    return str(getattr(settings, "TEACH_TOKEN", "") or os.environ.get("TEACH_TOKEN", "")).strip()


def _proxy_agent_learn(path, payload=None, timeout=8, admin_user=""):
    """Call the agent learn API. Returns (data, error_code). error_code is None on success."""
    origin = agent_learn_origin()
    if not origin:
        return None, "not_ready"
    headers = {
        "Accept": "application/json",
        "X-Teach-Token": agent_teach_token(),
    }
    if admin_user:
        headers["X-Admin-User"] = str(admin_user)[:64]
    data = None
    method = "GET"
    if payload is not None:
        method = "POST"
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        origin + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode() or "{}"
            return json.loads(raw), None
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 405, 501):
            return None, "not_ready"
        if exc.code in (401, 403):
            return None, "unauthorized"
        return None, "error"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None, "not_ready"


def _text_list(value, limit):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        items.append(text[:180])
        if len(items) >= limit:
            break
    return items


def _score_label(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.2f}"


def _clusters_from_inbox(data):
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("clusters") or data.get("items") or []
    else:
        rows = []
    clusters = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        questions = _text_list(row.get("questions"), 8)
        if not questions and row.get("question"):
            questions = _text_list([row.get("question")], 8)
        chat_id = str(row.get("chat_id") or row.get("item_id") or row.get("id") or "").strip()
        if not chat_id or not questions:
            continue
        label = str(row.get("label") or questions[0]).strip() or questions[0]
        count = row.get("count")
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = len(questions)
        clusters.append({
            "chat_id": chat_id[:80],
            "label": label[:140],
            "score_label": _score_label(row.get("needs_training_score", row.get("score"))),
            "count": max(count, 1),
            "questions": questions,
            "answer": str(row.get("answer") or row.get("sample_answer") or "").strip()[:2000],
            "signals": _text_list(row.get("signals") or row.get("reasons"), 6),
        })
    return clusters


TRAINING_NOTICES = {
    "not_ready": "The agent inbox is not connected yet. Questions will show up here once that service is available.",
    "unauthorized": "The agent refused the admin token.",
    "error": "The agent inbox could not be loaded.",
}


@superuser_required
def training_inbox(request):
    data, error = _proxy_agent_learn(
        "/learn/inbox",
        admin_user=getattr(request.user, "username", "") or "",
    )
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    return render(request, "harrison/training.html", {
        "clusters": [] if error else _clusters_from_inbox(data),
        "notice": TRAINING_NOTICES.get(error, ""),
        "unread_count": unread_count,
    })


@superuser_required
@require_POST
def training_reward(request):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Could not read that action."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Could not read that action."}, status=400)
    action = str(payload.get("action") or "").strip()
    if action not in ("approve", "edit", "reject"):
        return JsonResponse({"detail": "Choose approve, edit, or reject."}, status=400)
    chat_id = str(payload.get("chat_id") or payload.get("item_id") or "").strip()
    if not chat_id or len(chat_id) > 80:
        return JsonResponse({"detail": "Missing question id."}, status=400)
    answer = str(payload.get("answer") or "").strip()
    if action == "edit" and not answer:
        return JsonResponse({"detail": "Write the answer you want taught."}, status=400)
    if len(answer) > 2000:
        return JsonResponse({"detail": "That answer is too long."}, status=400)
    # Browser payload must not supply the teach token. Attach it only on the server.
    body = {
        "chat_id": chat_id,
        "item_id": chat_id,
        "action": action,
    }
    if answer:
        body["answer"] = answer
    data, error = _proxy_agent_learn(
        "/learn/reward",
        body,
        admin_user=getattr(request.user, "username", "") or "",
    )
    if error == "not_ready":
        return JsonResponse(
            {"ok": False, "stub": True, "detail": "The agent reward API is not ready yet."},
            status=503,
        )
    if error == "unauthorized":
        return JsonResponse({"ok": False, "detail": "The agent refused the admin token."}, status=502)
    if error or not isinstance(data, dict):
        return JsonResponse({"ok": False, "detail": "The agent could not save that review."}, status=502)
    if data.get("ok") is False:
        return JsonResponse({"ok": False, "detail": "The agent could not save that review."}, status=502)
    return JsonResponse({"ok": True})


# ─────────────────────────────────────────────
# PROJECTS CRUD
# ─────────────────────────────────────────────
@superuser_required
def project_list(request):
    projects = Project.objects.all()
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    return render(request, 'harrison/project_list.html', {
        'projects': projects,
        'unread_count': unread_count,
    })


@superuser_required
def project_create(request):
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        tags = request.POST.get('tags', '').strip()
        url = request.POST.get('url', '').strip()
        url_label = request.POST.get('url_label', 'View Project').strip()
        color = request.POST.get('color', 'violet')
        order = request.POST.get('order', 0)
        bg_image = request.FILES.get('bg_image')

        if not title or not description:
            messages.error(request, 'Title and description are required.')
        else:
            project = Project(
                title=title, description=description, tags=tags,
                url=url, url_label=url_label, color=color, order=order,
            )
            if bg_image:
                project.bg_image = bg_image
            project.save()
            messages.success(request, f'Project "{title}" created successfully.')
            return redirect('project_list')

    return render(request, 'harrison/project_form.html', {
        'form_title': 'Create Project',
        'action': 'create',
        'unread_count': unread_count,
        'color_choices': Project.COLORS,
    })


@superuser_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    unread_count = ContactMessage.objects.filter(is_read=False).count()

    if request.method == 'POST':
        project.title = request.POST.get('title', '').strip()
        project.description = request.POST.get('description', '').strip()
        project.tags = request.POST.get('tags', '').strip()
        project.url = request.POST.get('url', '').strip()
        project.url_label = request.POST.get('url_label', 'View Project').strip()
        project.color = request.POST.get('color', 'violet')
        project.order = request.POST.get('order', 0)

        if not project.title or not project.description:
            messages.error(request, 'Title and description are required.')
        else:
            bg_image = request.FILES.get('bg_image')
            if bg_image:
                project.bg_image = bg_image
            # Handle BG removal
            if request.POST.get('remove_bg') == '1' and project.bg_image:
                project.bg_image.delete(save=False)
                project.bg_image = None
            project.save()
            messages.success(request, f'Project "{project.title}" updated.')
            return redirect('project_list')

    return render(request, 'harrison/project_form.html', {
        'form_title': 'Edit Project',
        'action': 'edit',
        'project': project,
        'unread_count': unread_count,
        'color_choices': Project.COLORS,
    })


@superuser_required
@require_POST
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    name = project.title
    project.delete()
    return JsonResponse({'success': True, 'name': name})


# ─────────────────────────────────────────────
# GALLERY (existing, kept)
# ─────────────────────────────────────────────
@login_required
def upload_image(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'projects')
        image_file = request.FILES.get('image')
        if image_file:
            img = GalleryImage.objects.create(
                title=title, description=description,
                category=category, image=image_file, uploaded_by=request.user,
            )
            return JsonResponse({
                'success': True, 'id': img.id, 'title': img.title,
                'url': img.image.url, 'category': img.category,
                'description': img.description,
            })
        return JsonResponse({'error': 'No image provided'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@require_POST
def toggle_like(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    like, created = ImageLike.objects.get_or_create(image=image, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'count': image.like_count()})


@login_required
@require_POST
def add_comment(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    data = json.loads(request.body)
    text = data.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Empty comment'}, status=400)
    comment = ImageComment.objects.create(image=image, user=request.user, text=text)
    return JsonResponse({
        'id': comment.id,
        'user': request.user.get_full_name() or request.user.username,
        'text': comment.text,
        'created_at': comment.created_at.strftime('%b %d, %Y'),
    })


def get_image_data(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    comments = [{
        'id': c.id,
        'user': c.user.get_full_name() or c.user.username,
        'text': c.text,
        'created_at': c.created_at.strftime('%b %d, %Y'),
    } for c in image.comments.all()]
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ImageLike.objects.filter(image=image, user=request.user).exists()
    return JsonResponse({
        'id': image.id, 'title': image.title, 'description': image.description,
        'url': image.image.url, 'like_count': image.like_count(),
        'user_liked': user_liked, 'comments': comments,
    })


@require_POST
def send_message(request):
    data = json.loads(request.body)
    message_text = data.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    msg = ContactMessage(message=message_text)
    if request.user.is_authenticated:
        msg.sender = request.user
    else:
        msg.email = data.get('email', '').strip() or None
        msg.name = data.get('name', '').strip() or 'Anonymous'
    msg.save()
    return JsonResponse({'success': True})


@login_required
def upload_project_bg(request, project_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        bg_image = request.FILES.get('bg_image')
        if bg_image:
            project.bg_image = bg_image
            project.save()
            return JsonResponse({'success': True, 'url': project.bg_image.url})
        return JsonResponse({'error': 'No image provided'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)
