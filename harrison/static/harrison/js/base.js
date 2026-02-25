// ============================================================
// BASE.JS — Harrison Muraya Portfolio
// ============================================================

// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

// ===== MOBILE MENU =====
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
if (mobileMenuBtn && mobileMenu) {
  mobileMenuBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('open');
  });
  // Close on link click
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => mobileMenu.classList.remove('open'));
  });
}

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href === '#') return;
    const target = document.querySelector(href);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ===== SECTION REVEAL (Intersection Observer) =====
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active');
    }
  });
}, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });

document.querySelectorAll('.section-reveal').forEach(el => revealObserver.observe(el));

// ===== SKILL BARS =====
const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const bar = entry.target;
      const targetWidth = bar.style.width;
      bar.style.width = '0';
      requestAnimationFrame(() => {
        setTimeout(() => { bar.style.width = targetWidth; }, 80);
      });
      skillObserver.unobserve(bar);
    }
  });
}, { threshold: 0.4 });

document.querySelectorAll('.skill-bar').forEach(bar => skillObserver.observe(bar));

// ===== GALLERY FILTER =====
const filterBtns = document.querySelectorAll('.gallery-filter');
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.gallery-item').forEach(item => {
      const match = filter === 'all' || item.dataset.category === filter;
      item.style.display = match ? '' : 'none';
    });
  });
});

// ===== IMAGE VIEWER =====
let currentImageId = null;
let galleryIds = [];

function openViewer(id) {
  if (!id || id === 'placeholder') return;
  currentImageId = id;

  // Build ordered list of real gallery item IDs visible right now
  galleryIds = Array.from(
    document.querySelectorAll('.gallery-item[data-id]')
  )
    .filter(el => el.dataset.id !== 'placeholder' && el.style.display !== 'none')
    .map(el => parseInt(el.dataset.id));

  const viewer = document.getElementById('imageViewer');
  viewer.classList.add('open');
  document.body.style.overflow = 'hidden';
  loadImageData(id);
}

function closeViewer() {
  const viewer = document.getElementById('imageViewer');
  viewer.classList.remove('open');
  document.body.style.overflow = '';
  currentImageId = null;
}

function navigateViewer(dir) {
  if (!currentImageId || !galleryIds.length) return;
  const idx = galleryIds.indexOf(parseInt(currentImageId));
  if (idx === -1) return;
  const newIdx = (idx + dir + galleryIds.length) % galleryIds.length;
  currentImageId = galleryIds[newIdx];
  loadImageData(currentImageId);
}

async function loadImageData(id) {
  const commentsList = document.getElementById('commentsList');
  if (commentsList) {
    commentsList.innerHTML = '<p class="no-comments-msg">Loading…</p>';
  }

  try {
    const res = await fetch(`/image-data/${id}/`);
    const data = await res.json();

    const viewerImg = document.getElementById('viewerImage');
    const viewerTitle = document.getElementById('viewerTitle');
    const viewerDesc = document.getElementById('viewerDesc');
    const likeCount = document.getElementById('likeCount');
    const likeBtn = document.getElementById('likeBtn');

    if (viewerImg) viewerImg.src = data.url;
    if (viewerTitle) viewerTitle.textContent = data.title;
    if (viewerDesc) viewerDesc.textContent = data.description || '';
    if (likeCount) likeCount.textContent = data.like_count;

    if (likeBtn) {
      likeBtn.dataset.id = id;
      likeBtn.classList.toggle('liked', data.user_liked);
    }

    if (commentsList) {
      if (data.comments.length === 0) {
        commentsList.innerHTML = '<p class="no-comments-msg">No comments yet. Be the first!</p>';
      } else {
        commentsList.innerHTML = data.comments.map(c => `
          <div class="comment-bubble">
            <div class="comment-meta">
              <div class="comment-avatar">${c.user.charAt(0).toUpperCase()}</div>
              <span class="comment-user">${escapeHtml(c.user)}</span>
              <span class="comment-date">${c.created_at}</span>
            </div>
            <p class="comment-text">${escapeHtml(c.text)}</p>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load image data:', err);
    const commentsList = document.getElementById('commentsList');
    if (commentsList) {
      commentsList.innerHTML = '<p class="no-comments-msg">Failed to load.</p>';
    }
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function toggleLike() {
  if (!IS_AUTHENTICATED) {
    window.location.href = '/login/';
    return;
  }
  const likeBtn = document.getElementById('likeBtn');
  const id = likeBtn?.dataset.id || currentImageId;
  if (!id) return;

  try {
    const res = await fetch(`/toggle-like/${id}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });
    const data = await res.json();
    document.getElementById('likeCount').textContent = data.count;
    likeBtn.classList.toggle('liked', data.liked);
    showToast(data.liked ? '♥ Liked' : 'Unliked');
  } catch (err) {
    console.error(err);
  }
}

async function submitComment() {
  if (!IS_AUTHENTICATED) {
    window.location.href = '/login/';
    return;
  }
  const input = document.getElementById('commentInput');
  const text = (input?.value || '').trim();
  if (!text) return;

  const btn = document.querySelector('.btn-post');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`/add-comment/${currentImageId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.id) {
      input.value = '';
      await loadImageData(currentImageId);
      showToast('Comment posted');
    }
  } catch (err) {
    console.error(err);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Comment input — submit on Enter
const commentInputEl = document.getElementById('commentInput');
if (commentInputEl) {
  commentInputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitComment();
    }
  });
}

// Close viewer on backdrop click (outside sidebar and image)
document.getElementById('imageViewer')?.addEventListener('click', function (e) {
  if (e.target === this) closeViewer();
});

// Keyboard: Esc, arrow keys
document.addEventListener('keydown', (e) => {
  const viewer = document.getElementById('imageViewer');
  if (viewer?.classList.contains('open')) {
    if (e.key === 'Escape') closeViewer();
    if (e.key === 'ArrowLeft') navigateViewer(-1);
    if (e.key === 'ArrowRight') navigateViewer(1);
  }
});

// ===== UPLOAD MODAL =====
function openUploadModal() {
  const modal = document.getElementById('uploadModal');
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeUploadModal() {
  const modal = document.getElementById('uploadModal');
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Close upload modal on backdrop click
document.getElementById('uploadModal')?.addEventListener('click', function (e) {
  if (e.target === this) closeUploadModal();
});

// Drop zone
const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('imageInput');
if (dropZone && imageInput) {
  dropZone.addEventListener('click', () => imageInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--ink)';
    dropZone.style.background = 'var(--cream-alt)';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '';
    dropZone.style.background = '';
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    dropZone.style.background = '';
    if (e.dataTransfer.files[0]) {
      imageInput.files = e.dataTransfer.files;
      document.getElementById('dropText').innerHTML =
        `<span style="font-weight:600;color:var(--ink);">📷 ${e.dataTransfer.files[0].name}</span>`;
    }
  });

  imageInput.addEventListener('change', () => {
    if (imageInput.files[0]) {
      document.getElementById('dropText').innerHTML =
        `<span style="font-weight:600;color:var(--ink);">📷 ${imageInput.files[0].name}</span>`;
    }
  });
}

document.getElementById('uploadForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();
  const submitBtn = this.querySelector('.btn-upload');
  if (submitBtn) { submitBtn.textContent = 'Uploading…'; submitBtn.disabled = true; }

  const formData = new FormData(this);
  try {
    const res = await fetch('/upload-image/', {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      showToast('Image uploaded');
      closeUploadModal();
      setTimeout(() => location.reload(), 800);
    } else {
      showToast('Upload failed: ' + (data.error || 'unknown error'));
    }
  } catch (err) {
    showToast('Upload failed');
  } finally {
    if (submitBtn) { submitBtn.textContent = 'Upload'; submitBtn.disabled = false; }
  }
});

// ===== CONTACT MESSAGE =====
async function submitMessage() {
  const messageText = document.getElementById('messageText')?.value.trim();
  if (!messageText) {
    showToast('Please write a message first');
    return;
  }

  const btn = document.getElementById('sendBtn');
  const status = document.getElementById('msgStatus');
  if (btn) { btn.textContent = 'Sending…'; btn.disabled = true; }

  const body = { message: messageText };
  if (!IS_AUTHENTICATED) {
    body.name = document.getElementById('guestName')?.value.trim() || '';
    body.email = document.getElementById('guestEmail')?.value.trim() || '';
  }

  try {
    const res = await fetch('/send-message/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.success) {
      showToast("Message sent — I'll get back to you soon");
      document.getElementById('messageText').value = '';
      if (!IS_AUTHENTICATED) {
        const nameEl = document.getElementById('guestName');
        const emailEl = document.getElementById('guestEmail');
        if (nameEl) nameEl.value = '';
        if (emailEl) emailEl.value = '';
      }
      if (status) {
        status.textContent = "✓ Message sent!";
        status.style.color = '#16a34a';
        setTimeout(() => { status.textContent = ''; }, 4000);
      }
    } else {
      showToast('Failed to send. Try again.');
    }
  } catch (err) {
    showToast('Failed to send. Try again.');
  } finally {
    if (btn) { btn.textContent = 'Send Message'; btn.disabled = false; }
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
