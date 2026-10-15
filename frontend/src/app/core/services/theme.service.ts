import { DOCUMENT, Injectable, effect, inject, signal } from '@angular/core';

export type Theme = 'dark' | 'light';

export const THEME_STORAGE_KEY = 'lms-rpa-theme';

/**
 * Tema claro/escuro da aplicação. Escuro é o padrão (dark-first, DXi Design Guide).
 * O tema inicial também é aplicado por um script no index.html, antes da primeira pintura.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);

  readonly theme = signal<Theme>(readStoredTheme());

  constructor() {
    effect(() => {
      const theme = this.theme();
      this.document.documentElement.setAttribute('data-theme', theme);
      try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
      } catch {
        // Armazenamento indisponível (ex.: navegação privada): o tema vale só para a sessão.
      }
    });
  }

  toggle(): void {
    this.theme.update((theme) => (theme === 'dark' ? 'light' : 'dark'));
  }
}

function readStoredTheme(): Theme {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}
