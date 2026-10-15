// Configuração do Tailwind + alternância de tema claro/escuro compartilhada pelos mocks.
// Deve ser carregado logo após o CDN do Tailwind, dentro do <head>, para evitar "piscar" o tema errado.

const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

tailwind.config = {
  theme: {
    extend: {
      colors: {
        appBg: token('app-bg'),
        surface: token('surface'),
        surfaceHover: token('surface-hover'),
        surfaceSunken: token('surface-sunken'),
        console: token('console'),
        borderSoft: token('border-soft'),
        fg: {
          DEFAULT: token('fg'),
          muted: token('fg-muted'),
          subtle: token('fg-subtle'),
          faint: token('fg-faint'),
        },
        brand: token('brand'),
        brandHover: token('brand-hover'),
        'on-brand': token('on-brand'),
        success: token('success'),
        warning: token('warning'),
        danger: token('danger'),
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
};

(function () {
  const STORAGE_KEY = 'lms-rpa-theme';
  const root = document.documentElement;

  function getStored() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* armazenamento indisponível */ }
  }

  // Dark-first: escuro é o padrão, a menos que o usuário já tenha escolhido o claro.
  apply(getStored() === 'light' ? 'light' : 'dark');

  document.addEventListener('click', (event) => {
    if (!event.target.closest('[data-theme-toggle]')) return;
    apply(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
  });
})();
