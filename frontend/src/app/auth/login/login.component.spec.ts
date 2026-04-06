import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, ActivatedRoute } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LoginComponent } from './login.component';
import { AuthStateService } from '../services/auth-state.service';
import { AuthApiService } from '../services/auth-api.service';
import { of, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { convertToParamMap } from '@angular/router';

describe('LoginComponent', () => {
  let authApiService: AuthApiService;
  let authStateService: AuthStateService;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([
          { path: 'tasks', component: {} as any },
          { path: 'login', component: {} as any },
          { path: 'register', component: {} as any },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthApiService,
        AuthStateService,
      ],
    }).compileComponents();

    authApiService = TestBed.inject(AuthApiService);
    authStateService = TestBed.inject(AuthStateService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  function createComponent() {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
    return fixture;
  }

  describe('form structure', () => {
    it('should render an email input field', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const emailInput = compiled.querySelector('input[type="email"], input[formControlName="email"]');
      expect(emailInput).not.toBeNull();
    });

    it('should render a password input field', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const passwordInput = compiled.querySelector('input[type="password"], input[formControlName="password"]');
      expect(passwordInput).not.toBeNull();
    });

    it('should render a submit button', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const submitBtn = compiled.querySelector('button[type="submit"]');
      expect(submitBtn).not.toBeNull();
    });
  });

  describe('on successful login', () => {
    it('should call AuthApiService.login with email and password', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const loginSpy = vi.spyOn(authApiService, 'login').mockReturnValue(of('token'));

      component.form.setValue({ email: 'user@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(loginSpy).toHaveBeenCalledWith('user@example.com', 'password123');
    });

    it('should call AuthStateService.setToken with the returned token', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      vi.spyOn(authApiService, 'login').mockReturnValue(of('login-token'));
      const setTokenSpy = vi.spyOn(authStateService, 'setToken');

      component.form.setValue({ email: 'user@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(setTokenSpy).toHaveBeenCalledWith('login-token');
    });

    it('should navigate to /tasks on success', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      vi.spyOn(authApiService, 'login').mockReturnValue(of('some-token'));
      const navigateSpy = vi.spyOn(router, 'navigate');

      component.form.setValue({ email: 'user@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(navigateSpy).toHaveBeenCalledWith(['/tasks']);
    });
  });

  describe('on 401 Unauthorized', () => {
    it('should set a single generic error (not field-specific)', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 401,
        error: { detail: 'Invalid credentials' },
      });
      vi.spyOn(authApiService, 'login').mockReturnValue(throwError(() => error));

      component.form.setValue({ email: 'user@example.com', password: 'wrongpass' });
      component.onSubmit();
      await fixture.whenStable();
      fixture.detectChanges();

      expect(component.genericError).not.toBeNull();
    });

    it('should not set errors on individual fields for 401', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 401,
        error: { detail: 'Invalid credentials' },
      });
      vi.spyOn(authApiService, 'login').mockReturnValue(throwError(() => error));

      component.form.setValue({ email: 'user@example.com', password: 'wrongpass' });
      component.onSubmit();
      await fixture.whenStable();

      expect(component.form.get('email')?.errors).toBeNull();
      expect(component.form.get('password')?.errors).toBeNull();
    });

    it('should not navigate on 401', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 401,
        error: { detail: 'Invalid credentials' },
      });
      vi.spyOn(authApiService, 'login').mockReturnValue(throwError(() => error));
      const navigateSpy = vi.spyOn(router, 'navigate');

      component.form.setValue({ email: 'user@example.com', password: 'wrongpass' });
      component.onSubmit();
      await fixture.whenStable();

      expect(navigateSpy).not.toHaveBeenCalledWith(['/tasks']);
    });
  });

  describe('session expiry notification', () => {
    it('should expose a sessionExpiry flag that can be set by the component', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      expect('sessionExpired' in component).toBe(true);
    });
  });

  describe('client-side form validation', () => {
    it('should not call login when form is invalid', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const loginSpy = vi.spyOn(authApiService, 'login');

      component.form.setValue({ email: '', password: '' });
      component.onSubmit();
      await fixture.whenStable();

      expect(loginSpy).not.toHaveBeenCalled();
    });

    it('should mark form as invalid when email is missing', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: '', password: 'password123' });
      expect(component.form.valid).toBe(false);
    });

    it('should mark form as invalid when password is missing', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: 'user@example.com', password: '' });
      expect(component.form.valid).toBe(false);
    });

    it('should mark form as valid with valid email and password', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: 'user@example.com', password: 'anypassword' });
      expect(component.form.valid).toBe(true);
    });
  });
});
