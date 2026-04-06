import { TestBed } from '@angular/core/testing';
import {
  HttpClient,
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthApiService } from './auth-api.service';
import { TokenResponse } from '../../shared/models/auth.model';

describe('AuthApiService', () => {
  let service: AuthApiService;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(AuthApiService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  describe('register', () => {
    it('should POST to /api/v1/auth/register with email and password', () => {
      const email = 'user@example.com';
      const password = 'securepass';

      service.register(email, password).subscribe();

      const req = httpTestingController.expectOne('/api/v1/auth/register');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email, password });
      req.flush({ access_token: 'token', token_type: 'bearer' });
    });

    it('should return the access_token from the response', () => {
      const expectedToken = 'jwt-access-token';
      let receivedToken: string | undefined;

      service.register('user@example.com', 'password123').subscribe((token) => {
        receivedToken = token;
      });

      const req = httpTestingController.expectOne('/api/v1/auth/register');
      const response: TokenResponse = { access_token: expectedToken, token_type: 'bearer' };
      req.flush(response);

      expect(receivedToken).toBe(expectedToken);
    });

    it('should propagate HTTP errors to the caller', () => {
      let errorReceived = false;

      service.register('taken@example.com', 'password123').subscribe({
        error: () => {
          errorReceived = true;
        },
      });

      const req = httpTestingController.expectOne('/api/v1/auth/register');
      req.flush({ detail: 'Email already in use' }, { status: 409, statusText: 'Conflict' });

      expect(errorReceived).toBe(true);
    });
  });

  describe('login', () => {
    it('should POST to /api/v1/auth/login with email and password', () => {
      const email = 'user@example.com';
      const password = 'securepass';

      service.login(email, password).subscribe();

      const req = httpTestingController.expectOne('/api/v1/auth/login');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email, password });
      req.flush({ access_token: 'token', token_type: 'bearer' });
    });

    it('should return the access_token from the response', () => {
      const expectedToken = 'login-jwt-token';
      let receivedToken: string | undefined;

      service.login('user@example.com', 'password123').subscribe((token) => {
        receivedToken = token;
      });

      const req = httpTestingController.expectOne('/api/v1/auth/login');
      const response: TokenResponse = { access_token: expectedToken, token_type: 'bearer' };
      req.flush(response);

      expect(receivedToken).toBe(expectedToken);
    });

    it('should propagate HTTP errors to the caller', () => {
      let errorReceived = false;

      service.login('user@example.com', 'wrongpassword').subscribe({
        error: () => {
          errorReceived = true;
        },
      });

      const req = httpTestingController.expectOne('/api/v1/auth/login');
      req.flush(
        { detail: 'Invalid credentials' },
        { status: 401, statusText: 'Unauthorized' }
      );

      expect(errorReceived).toBe(true);
    });
  });
});
