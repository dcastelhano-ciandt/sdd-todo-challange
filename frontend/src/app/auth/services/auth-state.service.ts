import { Injectable, signal, computed } from '@angular/core';

const AUTH_TOKEN_KEY = 'auth_token';

@Injectable({ providedIn: 'root' })
export class AuthStateService {
  private readonly _token = signal<string | null>(localStorage.getItem(AUTH_TOKEN_KEY));

  readonly token = this._token.asReadonly();

  readonly isAuthenticated = computed(() => this._token() !== null);

  setToken(token: string): void {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    this._token.set(token);
  }

  clearSession(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    this._token.set(null);
  }

  getToken(): string | null {
    return this._token();
  }
}
