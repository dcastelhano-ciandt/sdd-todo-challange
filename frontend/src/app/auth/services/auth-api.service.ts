import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { TokenResponse, UserProfile } from '../../shared/models/auth.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl || '';

  register(email: string, password: string): Observable<string> {
    return this.http
      .post<TokenResponse>(`${this.base}/api/v1/auth/register`, { email, password })
      .pipe(map((response) => response.access_token));
  }

  login(email: string, password: string): Observable<string> {
    return this.http
      .post<TokenResponse>(`${this.base}/api/v1/auth/login`, { email, password })
      .pipe(map((response) => response.access_token));
  }

  changePassword(currentPassword: string, newPassword: string): Observable<string> {
    return this.http
      .patch<TokenResponse>(`${this.base}/api/v1/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
      })
      .pipe(map((response) => response.access_token));
  }

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.base}/api/v1/auth/me`);
  }
}
