// ===== NAVBAR =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
});

const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
    mobileMenu.querySelectorAll('a').forEach(l => l.addEventListener('click', () => mobileMenu.classList.add('hidden')));
}

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
});

// ===== SECTION REVEAL =====
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('active'); });
}, { threshold: 0.08, rootMargin: '0px 0px -80px 0px' });
document.querySelectorAll('.section-reveal').forEach(s => revealObserver.observe(s));

// ===== SKILL BARS =====
const skillObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const w = entry.target.getAttribute('data-width') || entry.target.style.width;
            entry.target.setAttribute('data-width', w);
            entry.target.style.width = '0';
            requestAnimationFrame(() => setTimeout(() => entry.target.style.width = w, 100));
            skillObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });
document.querySelectorAll('.skill-bar').forEach(b => skillObserver.observe(b));

// ===== GALLERY FILTER =====
const filterBtns = document.querySelectorAll('.gallery-filter');
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        document.querySelectorAll('.gallery-item').forEach(item => {
            if (filter === 'all' || item.dataset.category === filter) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
});

// ===== IMAGE VIEWER =====
let currentImageId = null;
let galleryIds = [];

function openViewer(id) {
    if (id === 'placeholder') return;
    currentImageId = id;
    galleryIds = Array.from(document.querySelectorAll('.gallery-item[data-id]'))
        .filter(el => el.dataset.id !== 'placeholder')
        .map(el => parseInt(el.dataset.id));
    
    const viewer = document.getElementById('imageViewer');
    viewer.classList.remove('hidden');
    viewer.classList.add('open');
    document.body.style.overflow = 'hidden';
    loadImageData(id);
}

function closeViewer() {
    const viewer = document.getElementById('imageViewer');
    viewer.classList.add('hidden');
    viewer.classList.remove('open');
    document.body.style.overflow = '';
    currentImageId = null;
}

function navigateViewer(dir) {
    if (!currentImageId || !galleryIds.length) return;
    const idx = galleryIds.indexOf(parseInt(currentImageId));
    const newIdx = (idx + dir + galleryIds.length) % galleryIds.length;
    currentImageId = galleryIds[newIdx];
    loadImageData(currentImageId);
}

async function loadImageData(id) {
    try {
        const res = await fetch(`/image-data/${id}/`);
        const data = await res.json();
        document.getElementById('viewerImage').src = data.url;
        document.getElementById('viewerTitle').textContent = data.title;
        document.getElementById('viewerDesc').textContent = data.description || '';

        const likeCount = document.getElementById('likeCount');
        if (likeCount) likeCount.textContent = data.like_count;

        const likeBtn = document.getElementById('likeBtn');
        if (likeBtn) {
            likeBtn.dataset.id = id;
            likeBtn.classList.toggle('liked', data.user_liked);
        }

        const commentsList = document.getElementById('commentsList');
        if (commentsList) {
            if (data.comments.length === 0) {
                commentsList.innerHTML = '<p class="text-white/30 text-sm text-center py-4">No comments yet. Be the first!</p>';
            } else {
                commentsList.innerHTML = data.comments.map(c => `
                    <div class="comment-bubble">
                        <div class="flex items-center gap-2 mb-1">
                            <div class="w-6 h-6 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center text-white text-xs font-bold">${c.user[0].toUpperCase()}</div>
                            <span class="text-white/70 text-xs font-medium">${c.user}</span>
                            <span class="text-white/25 text-xs ml-auto">${c.created_at}</span>
                        </div>
                        <p class="text-white/60 text-sm leading-relaxed">${c.text}</p>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Failed to load image data:', err);
    }
}

async function toggleLike() {
    if (!IS_AUTHENTICATED) { window.location.href = '/login/'; return; }
    const likeBtn = document.getElementById('likeBtn');
    const id = likeBtn?.dataset.id || currentImageId;
    try {
        const res = await fetch(`/toggle-like/${id}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN }
        });
        const data = await res.json();
        document.getElementById('likeCount').textContent = data.count;
        likeBtn.classList.toggle('liked', data.liked);
        showToast(data.liked ? '❤️ Liked!' : '💔 Unliked');
    } catch (err) { console.error(err); }
}

async function submitComment() {
    if (!IS_AUTHENTICATED) { window.location.href = '/login/'; return; }
    const input = document.getElementById('commentInput');
    const text = input.value.trim();
    if (!text) return;
    try {
        const res = await fetch(`/add-comment/${currentImageId}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (data.id) {
            input.value = '';
            await loadImageData(currentImageId);
            showToast('💬 Comment posted!');
        }
    } catch (err) { console.error(err); }
}

document.getElementById('commentInput')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitComment(); }
});

// Close viewer on backdrop click
document.getElementById('imageViewer')?.addEventListener('click', function(e) {
    if (e.target === this) closeViewer();
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    const viewer = document.getElementById('imageViewer');
    if (viewer && !viewer.classList.contains('hidden')) {
        if (e.key === 'Escape') closeViewer();
        if (e.key === 'ArrowLeft') navigateViewer(-1);
        if (e.key === 'ArrowRight') navigateViewer(1);
    }
});

// ===== UPLOAD MODAL =====
function openUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}
function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Drop zone
const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('imageInput');
if (dropZone && imageInput) {
    dropZone.addEventListener('click', () => imageInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#7c3aed'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        if (e.dataTransfer.files[0]) {
            imageInput.files = e.dataTransfer.files;
            document.getElementById('dropText').innerHTML = `<p class="text-violet-300 text-sm">📷 ${e.dataTransfer.files[0].name}</p>`;
        }
    });
    imageInput.addEventListener('change', () => {
        if (imageInput.files[0]) {
            document.getElementById('dropText').innerHTML = `<p class="text-violet-300 text-sm">📷 ${imageInput.files[0].name}</p>`;
        }
    });
}

document.getElementById('uploadForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    try {
        const res = await fetch('/upload-image/', {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast('✅ Image uploaded!');
            closeUploadModal();
            setTimeout(() => window.location.reload(), 800);
        } else {
            showToast('❌ Upload failed: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        showToast('❌ Upload failed');
    }
});

// ===== CONTACT MESSAGE =====
async function submitMessage() {
    const messageText = document.getElementById('messageText').value.trim();
    if (!messageText) { showToast('⚠️ Please write a message first.'); return; }
    
    const btn = document.getElementById('sendBtn');
    btn.textContent = 'Sending...';
    btn.disabled = true;

    const body = { message: messageText };
    if (!IS_AUTHENTICATED) {
        body.name = document.getElementById('guestName')?.value.trim() || '';
        body.email = document.getElementById('guestEmail')?.value.trim() || '';
    }

    try {
        const res = await fetch('/send-message/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.success) {
            showToast('✅ Message sent! I\'ll get back to you soon.');
            document.getElementById('messageText').value = '';
            if (!IS_AUTHENTICATED) {
                document.getElementById('guestName').value = '';
                document.getElementById('guestEmail').value = '';
            }
        }
    } catch (err) {
        showToast('❌ Failed to send message. Try again.');
    } finally {
        btn.textContent = 'Send Message';
        btn.disabled = false;
    }
}

// ===== TOAST =====
let toastTimeout;
function showToast(message) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.remove('show'), 3000);
}

// Close upload modal on backdrop click
document.getElementById('uploadModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeUploadModal();
});
