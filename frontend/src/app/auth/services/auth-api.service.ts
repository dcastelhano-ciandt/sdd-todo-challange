import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { TokenResponse } from '../../shared/models/auth.model';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly http = inject(HttpClient);

  register(email: string, password: string): Observable<string> {
    return this.http
      .post<TokenResponse>('/api/v1/auth/register', { email, password })
      .pipe(map((response) => response.access_token));
  }

  login(email: string, password: string): Observable<string> {
    return this.http
      .post<TokenResponse>('/api/v1/auth/login', { email, password })
      .pipe(map((response) => response.access_token));
  }
}
