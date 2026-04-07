import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { RegisterComponent } from './register.component';
import { AuthStateService } from '../services/auth-state.service';
import { AuthApiService } from '../services/auth-api.service';
import { of, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';

describe('RegisterComponent', () => {
  let authApiService: AuthApiService;
  let authStateService: AuthStateService;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        provideRouter([
          { path: 'tasks', component: {} as any },
          { path: 'login', component: {} as any },
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
    const fixture = TestBed.createComponent(RegisterComponent);
    fixture.detectChanges();
    return fixture;
  }

  describe('form structure', () => {
    it('should render an email input field', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const emailInput = compiled.querySelector(
        'input[type="email"], input[formControlName="email"]',
      );
      expect(emailInput).not.toBeNull();
    });

    it('should render a password input field', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const passwordInput = compiled.querySelector(
        'input[type="password"], input[formControlName="password"]',
      );
      expect(passwordInput).not.toBeNull();
    });

    it('should render a submit button', () => {
      const fixture = createComponent();
      const compiled = fixture.nativeElement as HTMLElement;
      const submitBtn = compiled.querySelector('button[type="submit"]');
      expect(submitBtn).not.toBeNull();
    });
  });

  describe('on successful registration', () => {
    it('should call AuthApiService.register with email and password', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const registerSpy = vi.spyOn(authApiService, 'register').mockReturnValue(of('new-token'));

      component.form.setValue({ email: 'new@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(registerSpy).toHaveBeenCalledWith('new@example.com', 'password123');
    });

    it('should call AuthStateService.setToken with the returned token', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      vi.spyOn(authApiService, 'register').mockReturnValue(of('returned-token'));
      const setTokenSpy = vi.spyOn(authStateService, 'setToken');

      component.form.setValue({ email: 'new@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(setTokenSpy).toHaveBeenCalledWith('returned-token');
    });

    it('should navigate to /tasks on success', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      vi.spyOn(authApiService, 'register').mockReturnValue(of('some-token'));
      const navigateSpy = vi.spyOn(router, 'navigate');

      component.form.setValue({ email: 'new@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(navigateSpy).toHaveBeenCalledWith(['/tasks']);
    });
  });

  describe('on 409 Conflict (email in use)', () => {
    it('should set emailInUse error on the email form control', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 409,
        error: { detail: 'Email already in use' },
      });
      vi.spyOn(authApiService, 'register').mockReturnValue(throwError(() => error));

      component.form.setValue({ email: 'taken@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();
      fixture.detectChanges();

      const emailControl = component.form.get('email');
      expect(emailControl.errors).not.toBeNull();
      expect(emailControl.errors['emailInUse']).toBe(true);
    });

    it('should not navigate to /tasks on 409', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 409,
        error: { detail: 'Email already in use' },
      });
      vi.spyOn(authApiService, 'register').mockReturnValue(throwError(() => error));
      const navigateSpy = vi.spyOn(router, 'navigate');

      component.form.setValue({ email: 'taken@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();

      expect(navigateSpy).not.toHaveBeenCalledWith(['/tasks']);
    });
  });

  describe('on 422 Unprocessable Entity (validation errors)', () => {
    it('should set serverError on the component', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const error = new HttpErrorResponse({
        status: 422,
        error: {
          detail: [
            {
              loc: ['body', 'email'],
              msg: 'value is not a valid email address',
              type: 'value_error.email',
            },
          ],
        },
      });
      vi.spyOn(authApiService, 'register').mockReturnValue(throwError(() => error));

      component.form.setValue({ email: 'user@example.com', password: 'password123' });
      component.onSubmit();
      await fixture.whenStable();
      fixture.detectChanges();

      expect(component.serverError).not.toBeNull();
    });
  });

  describe('client-side form validation', () => {
    it('should not call register when form is invalid', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const registerSpy = vi.spyOn(authApiService, 'register');

      component.form.setValue({ email: '', password: '' });
      component.onSubmit();
      await fixture.whenStable();

      expect(registerSpy).not.toHaveBeenCalled();
    });

    it('should mark form as invalid when email is missing', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: '', password: 'password123' });
      expect(component.form.valid).toBe(false);
    });

    it('should mark form as invalid when password is shorter than 8 characters', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: 'user@example.com', password: 'short' });
      expect(component.form.valid).toBe(false);
    });

    it('should mark form as valid when email and password are valid', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.form.setValue({ email: 'user@example.com', password: 'validpassword' });
      expect(component.form.valid).toBe(true);
    });
  });
});
