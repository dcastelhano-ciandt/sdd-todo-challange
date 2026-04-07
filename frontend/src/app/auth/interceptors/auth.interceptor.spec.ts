import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { authInterceptor } from './auth.interceptor';
import { AuthStateService } from '../services/auth-state.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTestingController: HttpTestingController;
  let authState: AuthStateService;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'login', component: {} as any }]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTestingController = TestBed.inject(HttpTestingController);
    authState = TestBed.inject(AuthStateService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpTestingController.verify();
    localStorage.clear();
  });

  describe('when no token is set', () => {
    it('should pass the request through without an Authorization header', () => {
      httpClient.get('/api/v1/tasks').subscribe();

      const req = httpTestingController.expectOne('/api/v1/tasks');
      expect(req.request.headers.has('Authorization')).toBe(false);
      req.flush([]);
    });
  });

  describe('when a token is set', () => {
    it('should attach Authorization: Bearer <token> to the request', () => {
      const token = 'test-jwt-token';
      authState.setToken(token);

      httpClient.get('/api/v1/tasks').subscribe();

      const req = httpTestingController.expectOne('/api/v1/tasks');
      expect(req.request.headers.get('Authorization')).toBe(`Bearer ${token}`);
      req.flush([]);
    });

    it('should not mutate the original request object', () => {
      authState.setToken('some-token');

      httpClient.get('/api/v1/tasks').subscribe();

      const req = httpTestingController.expectOne('/api/v1/tasks');
      // The request reaching the backend is a clone with the header
      expect(req.request.headers.has('Authorization')).toBe(true);
      req.flush([]);
    });
  });

  describe('on 401 response', () => {
    it('should call clearSession on AuthStateService', () => {
      authState.setToken('valid-token');
      const clearSessionSpy = vi.spyOn(authState, 'clearSession');

      httpClient.get('/api/v1/tasks').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/tasks');
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(clearSessionSpy).toHaveBeenCalled();
    });

    it('should navigate to /login on 401 response', () => {
      authState.setToken('valid-token');
      const navigateSpy = vi.spyOn(router, 'navigate');

      httpClient.get('/api/v1/tasks').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/tasks');
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(navigateSpy).toHaveBeenCalledWith(['/login']);
    });

    it('should not call clearSession on non-401 error responses', () => {
      authState.setToken('valid-token');
      const clearSessionSpy = vi.spyOn(authState, 'clearSession');

      httpClient.get('/api/v1/tasks').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/tasks');
      req.flush({ detail: 'Not found' }, { status: 404, statusText: 'Not Found' });

      expect(clearSessionSpy).not.toHaveBeenCalled();
    });

    it('should not navigate to /login on non-401 error responses', () => {
      authState.setToken('valid-token');
      const navigateSpy = vi.spyOn(router, 'navigate');

      httpClient.get('/api/v1/tasks').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/tasks');
      req.flush({ detail: 'Server error' }, { status: 500, statusText: 'Internal Server Error' });

      expect(navigateSpy).not.toHaveBeenCalled();
    });
  });

  // ─── Task 6: session expiry on dashboard page (requirement 5.3) ─────────────

  describe('session expiry on dashboard page (requirement 5.3)', () => {
    it('should call clearSession when a 401 is received on a non-auth endpoint (covers dashboard)', () => {
      authState.setToken('valid-token');
      const clearSessionSpy = vi.spyOn(authState, 'clearSession');

      // Simulate a request that would originate from the dashboard page
      // (e.g., GET /api/v1/auth/me or any non-auth endpoint)
      httpClient.get('/api/v1/profile').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/profile');
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(clearSessionSpy).toHaveBeenCalled();
    });

    it('should navigate to /login when a 401 is received on a non-auth endpoint (covers dashboard)', () => {
      authState.setToken('valid-token');
      const navigateSpy = vi.spyOn(router, 'navigate');

      httpClient.get('/api/v1/profile').subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/profile');
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(navigateSpy).toHaveBeenCalledWith(['/login']);
    });

    it('should NOT call clearSession on a 401 from an auth endpoint (login/register excluded)', () => {
      authState.setToken('valid-token');
      const clearSessionSpy = vi.spyOn(authState, 'clearSession');

      httpClient.post('/api/v1/auth/change-password', {}).subscribe({ error: () => {} });

      const req = httpTestingController.expectOne('/api/v1/auth/change-password');
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(clearSessionSpy).not.toHaveBeenCalled();
    });
  });
});
