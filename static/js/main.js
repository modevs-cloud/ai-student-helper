document.addEventListener('DOMContentLoaded', () => {

  /* ── Session update helper ──────────────────────────────────── */
  window.updateSessionState = (key, val) => {
    fetch('/session_update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [key]: val })
    }).catch(err => console.error('Error updating session:', err));
  };

  /* ── Keep-alive ping (prevents Render from sleeping) ──────── */
  // Pings /ping every 10 minutes so the server never idles out
  const PING_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes
  function sendKeepAlivePing() {
    fetch('/ping', { method: 'GET', cache: 'no-store' })
      .then(r => r.ok && console.debug('Keep-alive ping OK'))
      .catch(() => {}); // silent — never show errors to user
  }
  // Initial ping after 30 seconds, then every 10 minutes
  setTimeout(() => {
    sendKeepAlivePing();
    setInterval(sendKeepAlivePing, PING_INTERVAL_MS);
  }, 30_000);

  /* ── Global fetch with 90-second timeout ───────────────────── */
  // Attach to window so dashboard and other pages can use it
  window.fetchWithTimeout = (url, options = {}, timeoutMs = 90_000) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(url, { ...options, signal: controller.signal })
      .finally(() => clearTimeout(id));
  };

  /* ── Theme toggle ──────────────────────────────────────────── */
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    const setTheme = (theme) => {
      document.documentElement.setAttribute('data-theme', theme);
      toggleBtn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
      toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
    };

    // Init icon based on current theme
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    toggleBtn.textContent = current === 'dark' ? '☀️' : '🌙';
    toggleBtn.setAttribute('aria-label', `Switch to ${current === 'dark' ? 'light' : 'dark'} mode`);

    toggleBtn.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(next);
      window.updateSessionState('theme', next);
    });
  }

  /* ── Intersection Observer — scroll reveals ─────────────────── */
  const revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, i) => {
          if (entry.isIntersecting) {
            // Stagger each card slightly
            setTimeout(() => {
              entry.target.classList.add('visible');
            }, i * 80);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach((el) => observer.observe(el));
  }

  /* ── Navbar shadow on scroll ────────────────────────────────── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 20
        ? '0 4px 24px rgba(0,0,0,0.35)'
        : 'none';
    }, { passive: true });
  }

  /* ── Hamburger / mobile menu ────────────────────────────────── */
  const hamburgerBtn = document.getElementById('hamburger-btn');
  const mobileMenu   = document.getElementById('mobile-menu');

  const openMenu = () => {
    hamburgerBtn.classList.add('open');
    mobileMenu.classList.add('open');
    hamburgerBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden'; // prevent background scroll
  };

  const closeMenu = () => {
    hamburgerBtn.classList.remove('open');
    mobileMenu.classList.remove('open');
    hamburgerBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };

  if (hamburgerBtn && mobileMenu) {
    hamburgerBtn.addEventListener('click', () => {
      hamburgerBtn.classList.contains('open') ? closeMenu() : openMenu();
    });

    // Close when any mobile nav link is clicked
    mobileMenu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', closeMenu);
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeMenu();
    });
  }

  /* ── Google Sign In button — ripple effect ──────────────────── */
  const googleBtn = document.getElementById('google-signin-btn');
  if (googleBtn) {
    googleBtn.addEventListener('click', (e) => {
      // Create ripple
      const ripple = document.createElement('span');
      ripple.style.cssText = `
        position: absolute;
        width: 8px; height: 8px;
        background: rgba(255,255,255,0.4);
        border-radius: 50%;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%) scale(0);
        animation: ripple-expand 0.5s ease-out forwards;
        pointer-events: none;
      `;
      googleBtn.style.position = 'relative';
      googleBtn.style.overflow = 'hidden';
      googleBtn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }

});

/* ── Inject ripple keyframes dynamically ───────────────────── */
const style = document.createElement('style');
style.textContent = `
  @keyframes ripple-expand {
    to { transform: translate(-50%, -50%) scale(25); opacity: 0; }
  }
`;
document.head.appendChild(style);
