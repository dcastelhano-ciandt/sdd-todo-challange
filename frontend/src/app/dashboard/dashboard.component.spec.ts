import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DashboardComponent, passwordsMatchValidator } from './dashboard.component';
import { AuthApiService } from '../auth/services/auth-api.service';
import { AuthStateService } from '../auth/services/auth-state.service';
import { of, throwError, Subject } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { UserProfile } from '../shared/models/auth.model';
import { AbstractControl, FormGroup } from '@angular/forms';

describe('DashboardComponent — task 5.1 (skeleton, email display, profile loading)', () => {
  let authApiService: AuthApiService;

  beforeEach(async () => {
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([
          { path: 'login', component: {} as any },
          { path: 'dashboard', component: {} as any },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthApiService,
      ],
    }).compileComponents();

    authApiService = TestBed.inject(AuthApiService);
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  function createComponent() {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    return fixture;
  }

  // ─── Component structure ────────────────────────────────────────────────────

  describe('component structure', () => {
    it('should create the component', () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'user@example.com' })
      );
      const fixture = createComponent();
      expect(fixture.componentInstance).toBeTruthy();
    });

    it('should render a text input for the email field', () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'user@example.com' })
      );
      const fixture = createComponent();
      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>(
        'input[type="text"][data-testid="email-input"], input[type="email"][data-testid="email-input"]'
      );
      expect(emailInput).not.toBeNull();
    });

    it('should render the email input with the disabled attribute (requirement 1.4)', () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'user@example.com' })
      );
      const fixture = createComponent();
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>(
        '[data-testid="email-input"]'
      );
      expect(emailInput).not.toBeNull();
      expect(emailInput!.disabled).toBe(true);
    });
  });

  // ─── Profile loading on init ────────────────────────────────────────────────

  describe('profile loading on init', () => {
    it('should call AuthApiService.getProfile on initialization', () => {
      const getProfileSpy = vi
        .spyOn(authApiService, 'getProfile')
        .mockReturnValue(of({ email: 'user@example.com' }));

      createComponent();

      expect(getProfileSpy).toHaveBeenCalledOnce();
    });

    it('should display the email returned by getProfile in the email input', async () => {
      const profile: UserProfile = { email: 'test@example.com' };
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(of(profile));

      const fixture = createComponent();
      await fixture.whenStable();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>(
        '[data-testid="email-input"]'
      );
      expect(emailInput).not.toBeNull();
      expect(emailInput!.value).toBe('test@example.com');
    });

    it('should expose the loaded email on the component instance', async () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'loaded@example.com' })
      );

      const fixture = createComponent();
      await fixture.whenStable();

      const component = fixture.componentInstance as any;
      expect(component.email).toBe('loaded@example.com');
    });
  });

  // ─── Profile loading failure ────────────────────────────────────────────────

  describe('profile loading failure (requirement 1.4 graceful error)', () => {
    it('should display a generic error message when getProfile fails', async () => {
      const error = new HttpErrorResponse({ status: 500, statusText: 'Server Error' });
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(throwError(() => error));

      const fixture = createComponent();
      await fixture.whenStable();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="profile-load-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should NOT leave the email input blank without showing an error when getProfile fails', async () => {
      const error = new HttpErrorResponse({ status: 500, statusText: 'Server Error' });
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(throwError(() => error));

      const fixture = createComponent();
      await fixture.whenStable();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>(
        '[data-testid="email-input"]'
      );
      const errorEl = el.querySelector('[data-testid="profile-load-error"]');

      // Either the email has a value OR an error message is shown — never silently blank
      const hasEmailValue = emailInput && emailInput.value.trim().length > 0;
      const hasErrorMessage = errorEl !== null;
      expect(hasEmailValue || hasErrorMessage).toBe(true);
    });

    it('should set profileLoadError on the component instance when getProfile fails', async () => {
      const error = new HttpErrorResponse({ status: 500, statusText: 'Server Error' });
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(throwError(() => error));

      const fixture = createComponent();
      await fixture.whenStable();

      const component = fixture.componentInstance as any;
      expect(component.profileLoadError).not.toBeNull();
    });

    it('should NOT show a profile error when getProfile succeeds', async () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'ok@example.com' })
      );

      const fixture = createComponent();
      await fixture.whenStable();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="profile-load-error"]');
      expect(errorEl).toBeNull();
    });
  });

  // ─── Standalone component metadata ─────────────────────────────────────────

  describe('component metadata', () => {
    it('should be a standalone component', () => {
      // Angular standalone components have standalone: true in their metadata.
      // TestBed.createComponent works for standalone components without declaring them.
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(
        of({ email: 'user@example.com' })
      );
      const fixture = createComponent();
      // If it renders without error, standalone: true is configured correctly.
      expect(fixture.nativeElement).toBeTruthy();
    });
  });
});

// ─── Task 5.2: Change-password reactive form ────────────────────────────────

describe('DashboardComponent — task 5.2 (change-password reactive form)', () => {
  let authApiService: AuthApiService;

  beforeEach(async () => {
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([
          { path: 'login', component: {} as any },
          { path: 'dashboard', component: {} as any },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthApiService,
      ],
    }).compileComponents();

    authApiService = TestBed.inject(AuthApiService);
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  function createComponent() {
    vi.spyOn(authApiService, 'getProfile').mockReturnValue(
      of({ email: 'user@example.com' })
    );
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    return fixture;
  }

  // ─── passwordsMatchValidator (unit) ────────────────────────────────────────

  describe('passwordsMatchValidator', () => {
    it('should return null (no error) when newPassword and confirmNewPassword match', () => {
      const group = {
        get: (name: string) => {
          const values: Record<string, { value: string }> = {
            newPassword: { value: 'validPass1' },
            confirmNewPassword: { value: 'validPass1' },
          };
          return values[name] ?? null;
        },
      } as unknown as AbstractControl;

      const result = passwordsMatchValidator(group);
      expect(result).toBeNull();
    });

    it('should return { passwordsMismatch: true } when newPassword and confirmNewPassword differ', () => {
      const group = {
        get: (name: string) => {
          const values: Record<string, { value: string }> = {
            newPassword: { value: 'password1' },
            confirmNewPassword: { value: 'differentPass' },
          };
          return values[name] ?? null;
        },
      } as unknown as AbstractControl;

      const result = passwordsMatchValidator(group);
      expect(result).toEqual({ passwordsMismatch: true });
    });

    it('should return null when both passwords are empty strings (both blank)', () => {
      const group = {
        get: (name: string) => {
          const values: Record<string, { value: string }> = {
            newPassword: { value: '' },
            confirmNewPassword: { value: '' },
          };
          return values[name] ?? null;
        },
      } as unknown as AbstractControl;

      const result = passwordsMatchValidator(group);
      expect(result).toBeNull();
    });
  });

  // ─── Form structure (requirement 2.1, 2.2) ─────────────────────────────────

  describe('form structure', () => {
    it('should render a password input for current password (type="password")', () => {
      const fixture = createComponent();
      const el: HTMLElement = fixture.nativeElement;
      const input = el.querySelector<HTMLInputElement>(
        'input[type="password"][formControlName="currentPassword"], input[type="password"][data-testid="current-password-input"]'
      );
      expect(input).not.toBeNull();
    });

    it('should render a password input for new password (type="password")', () => {
      const fixture = createComponent();
      const el: HTMLElement = fixture.nativeElement;
      const input = el.querySelector<HTMLInputElement>(
        'input[type="password"][formControlName="newPassword"], input[type="password"][data-testid="new-password-input"]'
      );
      expect(input).not.toBeNull();
    });

    it('should render a password input for confirm new password (type="password")', () => {
      const fixture = createComponent();
      const el: HTMLElement = fixture.nativeElement;
      const input = el.querySelector<HTMLInputElement>(
        'input[type="password"][formControlName="confirmNewPassword"], input[type="password"][data-testid="confirm-password-input"]'
      );
      expect(input).not.toBeNull();
    });

    it('should render a submit button (requirement 2.3)', () => {
      const fixture = createComponent();
      const el: HTMLElement = fixture.nativeElement;
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
    });

    it('should expose a changePasswordForm FormGroup on the component instance', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      expect(component.changePasswordForm).toBeDefined();
      expect(component.changePasswordForm instanceof FormGroup).toBe(true);
    });

    it('should have currentPassword, newPassword, and confirmNewPassword controls', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      expect(form.contains('currentPassword')).toBe(true);
      expect(form.contains('newPassword')).toBe(true);
      expect(form.contains('confirmNewPassword')).toBe(true);
    });
  });

  // ─── Required validators (requirement 3.1) ─────────────────────────────────

  describe('required field validation (requirement 3.1)', () => {
    it('should mark the form invalid when currentPassword is empty', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: '',
        newPassword: 'validPass1',
        confirmNewPassword: 'validPass1',
      });

      expect(form.get('currentPassword')?.hasError('required')).toBe(true);
      expect(form.valid).toBe(false);
    });

    it('should mark the form invalid when newPassword is empty', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'currentPass1',
        newPassword: '',
        confirmNewPassword: '',
      });

      expect(form.get('newPassword')?.hasError('required')).toBe(true);
      expect(form.valid).toBe(false);
    });

    it('should mark the form invalid when confirmNewPassword is empty', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'currentPass1',
        newPassword: 'validPass1',
        confirmNewPassword: '',
      });

      expect(form.get('confirmNewPassword')?.hasError('required')).toBe(true);
      expect(form.valid).toBe(false);
    });
  });

  // ─── Min-length validators (requirement 3.3) ───────────────────────────────

  describe('minLength(8) validation on newPassword and confirmNewPassword (requirement 3.3)', () => {
    it('should mark newPassword invalid when it has fewer than 8 characters', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'short',
        confirmNewPassword: 'short',
      });

      expect(form.get('newPassword')?.hasError('minlength')).toBe(true);
    });

    it('should mark confirmNewPassword invalid when it has fewer than 8 characters', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'short',
        confirmNewPassword: 'short',
      });

      expect(form.get('confirmNewPassword')?.hasError('minlength')).toBe(true);
    });

    it('should NOT apply minLength to currentPassword', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'short',
        newPassword: 'validpassword',
        confirmNewPassword: 'validpassword',
      });

      expect(form.get('currentPassword')?.hasError('minlength')).toBe(false);
    });

    it('should not show minlength error for newPassword when value is at least 8 characters', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'validpass',
        confirmNewPassword: 'validpass',
      });

      expect(form.get('newPassword')?.hasError('minlength')).toBe(false);
    });
  });

  // ─── Cross-field mismatch validator (requirement 3.2) ──────────────────────

  describe('cross-field passwordsMismatch validator (requirement 3.2)', () => {
    it('should set passwordsMismatch error on the group when passwords differ', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newPassword1',
        confirmNewPassword: 'differentPass',
      });

      expect(form.hasError('passwordsMismatch')).toBe(true);
    });

    it('should clear passwordsMismatch error when passwords match', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'matchingPass1',
        confirmNewPassword: 'matchingPass1',
      });

      expect(form.hasError('passwordsMismatch')).toBe(false);
    });

    it('should keep the form invalid when passwords differ even if all fields are filled and long enough', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newPassword1',
        confirmNewPassword: 'newPassword2',
      });

      expect(form.valid).toBe(false);
    });
  });

  // ─── Form validity for submit (requirement 3.4) ────────────────────────────

  describe('form validity and submit button state (requirement 3.4)', () => {
    it('should mark the form valid when all fields are filled, passwords match, and meet min-length', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newValidPass1',
        confirmNewPassword: 'newValidPass1',
      });

      expect(form.valid).toBe(true);
    });

    it('should disable the submit button when the form is invalid', () => {
      const fixture = createComponent();
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;

      // Form starts empty so it is invalid
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(true);
    });

    it('should enable the submit button when the form is valid', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newValidPass1',
        confirmNewPassword: 'newValidPass1',
      });

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(false);
    });

    it('should disable the submit button when submitting is true even if form is valid', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newValidPass1',
        confirmNewPassword: 'newValidPass1',
      });
      component.submitting = true;

      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(true);
    });

    // ─── Task 8.1: additional submit-button disabled states ───────────────────

    it('should disable the submit button when passwords are shorter than 8 characters (req 3.3)', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'short',
        confirmNewPassword: 'short',
      });

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(true);
    });

    it('should disable the submit button when passwords do not match (req 3.2)', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.setValue({
        currentPassword: 'current1',
        newPassword: 'newPassword1',
        confirmNewPassword: 'differentPass',
      });

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const btn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(true);
    });
  });

  // ─── Inline error messages (requirement 3.1, 3.2, 3.3) ────────────────────

  describe('inline error messages', () => {

    it('should show required error for currentPassword when touched and empty', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('currentPassword')?.markAsTouched();
      form.get('currentPassword')?.setValue('');

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="current-password-required-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should show required error for newPassword when touched and empty', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('newPassword')?.markAsTouched();
      form.get('newPassword')?.setValue('');

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="new-password-required-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should show required error for confirmNewPassword when touched and empty', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('confirmNewPassword')?.markAsTouched();
      form.get('confirmNewPassword')?.setValue('');

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="confirm-password-required-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should show minlength error for newPassword when touched and too short', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('newPassword')?.markAsTouched();
      form.get('newPassword')?.setValue('short');

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="new-password-minlength-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should show mismatch error beneath confirmNewPassword when passwords differ and confirmNewPassword is touched', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('confirmNewPassword')?.markAsTouched();
      form.setValue({
        currentPassword: 'current1',
        newPassword: 'password1A',
        confirmNewPassword: 'password2B',
      });

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="passwords-mismatch-error"]');
      expect(errorEl).not.toBeNull();
      expect(errorEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should NOT show mismatch error when passwords match', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      form.get('confirmNewPassword')?.markAsTouched();
      form.setValue({
        currentPassword: 'current1',
        newPassword: 'matching1',
        confirmNewPassword: 'matching1',
      });

      fixture.detectChanges();
      await fixture.whenStable();

      const el: HTMLElement = fixture.nativeElement;
      const errorEl = el.querySelector('[data-testid="passwords-mismatch-error"]');
      expect(errorEl).toBeNull();
    });
  });
});

// ─── Task 5.3: Form submission, loading state, and result handling ─────────

describe('DashboardComponent — task 5.3 (form submission, loading state, result handling)', () => {
  let authApiService: AuthApiService;
  let authStateService: AuthStateService;

  beforeEach(async () => {
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([
          { path: 'login', component: {} as any },
          { path: 'dashboard', component: {} as any },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthApiService,
        AuthStateService,
      ],
    }).compileComponents();

    authApiService = TestBed.inject(AuthApiService);
    authStateService = TestBed.inject(AuthStateService);
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  function createComponent() {
    vi.spyOn(authApiService, 'getProfile').mockReturnValue(
      of({ email: 'user@example.com' })
    );
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    return fixture;
  }

  function fillValidForm(fixture: ReturnType<typeof createComponent>) {
    const component = fixture.componentInstance as any;
    const form: FormGroup = component.changePasswordForm;
    form.setValue({
      currentPassword: 'oldPassword1',
      newPassword: 'newPassword1',
      confirmNewPassword: 'newPassword1',
    });
    fixture.detectChanges();
    return form;
  }

  // ─── submitting flag and button disabled during request (requirement 4.5) ─

  describe('submitting flag and button loading state (requirement 4.5)', () => {
    it('should set submitting to true when form is submitted', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      // Mock changePassword to never resolve during this test
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        new Subject<string>().asObservable()
      );

      component.onChangePassword();

      expect(component.submitting).toBe(true);
    });

    it('should disable the submit button while submitting', async () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(of({ email: 'user@example.com' }));
      const fixture = TestBed.createComponent(DashboardComponent);
      // Enable auto-detection before initial render so all subsequent changes are tracked
      fixture.autoDetectChanges(true);
      await fixture.whenStable();

      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      const subject = new Subject<string>();
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(subject.asObservable());

      // Run inside the Angular zone so auto change detection fires
      fixture.ngZone!.run(() => {
        form.setValue({
          currentPassword: 'oldPassword1',
          newPassword: 'newPassword1',
          confirmNewPassword: 'newPassword1',
        });
        component.onChangePassword();
      });
      await fixture.whenStable();

      const btn = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
        'button[type="submit"]'
      );
      expect(btn).not.toBeNull();
      expect(btn!.disabled).toBe(true);
    });

    it('should display a loading label on the button while submitting', async () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(of({ email: 'user@example.com' }));
      const fixture = TestBed.createComponent(DashboardComponent);
      fixture.autoDetectChanges(true);
      await fixture.whenStable();

      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      const subject = new Subject<string>();
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(subject.asObservable());

      fixture.ngZone!.run(() => {
        form.setValue({
          currentPassword: 'oldPassword1',
          newPassword: 'newPassword1',
          confirmNewPassword: 'newPassword1',
        });
        component.onChangePassword();
      });
      await fixture.whenStable();

      const btn = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
        'button[type="submit"]'
      );
      expect(btn!.textContent!.trim().length).toBeGreaterThan(0);
      // The label while submitting should differ from the idle label
      expect(btn!.textContent!.trim()).not.toBe('Change Password');
    });
  });

  // ─── Calls AuthApiService.changePassword with correct arguments ────────────

  describe('API call (requirement 4.1)', () => {
    it('should call AuthApiService.changePassword with currentPassword and newPassword on submit', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      form.setValue({
        currentPassword: 'myOldPass1',
        newPassword: 'myNewPass1',
        confirmNewPassword: 'myNewPass1',
      });

      const changePasswordSpy = vi
        .spyOn(authApiService, 'changePassword')
        .mockReturnValue(of('new-token-string'));

      component.onChangePassword();

      expect(changePasswordSpy).toHaveBeenCalledWith('myOldPass1', 'myNewPass1');
    });

    it('should not call AuthApiService.changePassword when the form is invalid', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      form.setValue({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: '',
      });

      const changePasswordSpy = vi
        .spyOn(authApiService, 'changePassword')
        .mockReturnValue(of('new-token-string'));

      component.onChangePassword();

      expect(changePasswordSpy).not.toHaveBeenCalled();
    });
  });

  // ─── Success path (requirements 4.3, 4.4, 5.4) ────────────────────────────

  describe('success path (requirements 4.3, 4.4, 5.4)', () => {
    it('should call AuthStateService.setToken with the new token on success', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('fresh-token-abc'));
      const setTokenSpy = vi.spyOn(authStateService, 'setToken');

      component.onChangePassword();

      expect(setTokenSpy).toHaveBeenCalledWith('fresh-token-abc');
    });

    it('should display a success confirmation message on success', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('fresh-token-abc'));
      vi.spyOn(authStateService, 'setToken').mockImplementation(() => {});

      component.onChangePassword();
      fixture.detectChanges();
      await fixture.whenStable();

      // successMessage property must be set
      expect(component.successMessage).toBeTruthy();

      // The DOM must also render the message
      const el: HTMLElement = fixture.nativeElement;
      const msgEl = el.querySelector('[data-testid="success-message"]');
      expect(msgEl).not.toBeNull();
      expect(msgEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should reset the form (clear all password fields) on success', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      form.setValue({
        currentPassword: 'oldPassword1',
        newPassword: 'newPassword1',
        confirmNewPassword: 'newPassword1',
      });
      // Stabilize before acting
      fixture.detectChanges();

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('fresh-token-abc'));
      vi.spyOn(authStateService, 'setToken').mockImplementation(() => {});

      component.onChangePassword();
      await fixture.whenStable();

      // After reset, all control values should be empty/null
      expect(form.get('currentPassword')?.value).toBeFalsy();
      expect(form.get('newPassword')?.value).toBeFalsy();
      expect(form.get('confirmNewPassword')?.value).toBeFalsy();
    });

    it('should set submitting back to false after success', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('fresh-token-abc'));
      vi.spyOn(authStateService, 'setToken').mockImplementation(() => {});

      component.onChangePassword();
      await fixture.whenStable();

      expect(component.submitting).toBe(false);
    });
  });

  // ─── 401 (incorrect current password) (requirement 4.2) ───────────────────

  describe('401 incorrect current password (requirement 4.2)', () => {
    it('should display a specific error on the current password field for a 401 response', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error401 = new HttpErrorResponse({ status: 401, statusText: 'Unauthorized' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error401)
      );

      component.onChangePassword();
      fixture.detectChanges();
      await fixture.whenStable();

      // The current password field must carry an error set by the component
      const currentPwdControl = component.changePasswordForm.get('currentPassword');
      expect(currentPwdControl?.errors).toBeTruthy();
      expect(currentPwdControl?.hasError('incorrectPassword')).toBe(true);
    });

    it('should render the current-password-incorrect error message in the DOM for a 401', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error401 = new HttpErrorResponse({ status: 401, statusText: 'Unauthorized' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error401)
      );

      component.onChangePassword();
      fixture.detectChanges();
      await fixture.whenStable();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const errEl = el.querySelector('[data-testid="current-password-incorrect-error"]');
      expect(errEl).not.toBeNull();
      expect(errEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should NOT display a generic server error for a 401 (wrong current password)', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error401 = new HttpErrorResponse({ status: 401, statusText: 'Unauthorized' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error401)
      );

      component.onChangePassword();
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.serverError).toBeNull();
    });

    it('should set submitting back to false after a 401 error', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error401 = new HttpErrorResponse({ status: 401, statusText: 'Unauthorized' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error401)
      );

      component.onChangePassword();
      await fixture.whenStable();

      expect(component.submitting).toBe(false);
    });
  });

  // ─── Generic server error (4xx/5xx other than 401) ────────────────────────

  describe('generic server error for non-401 failures', () => {
    it('should display a generic error message for a 500 server error', async () => {
      vi.spyOn(authApiService, 'getProfile').mockReturnValue(of({ email: 'user@example.com' }));
      const fixture = TestBed.createComponent(DashboardComponent);
      fixture.autoDetectChanges(true);
      await fixture.whenStable();

      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;

      const error500 = new HttpErrorResponse({ status: 500, statusText: 'Internal Server Error' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error500)
      );

      // Run inside the zone so auto change detection fires after the error callback
      fixture.ngZone!.run(() => {
        form.setValue({
          currentPassword: 'oldPassword1',
          newPassword: 'newPassword1',
          confirmNewPassword: 'newPassword1',
        });
        component.onChangePassword();
      });
      await fixture.whenStable();

      expect(component.serverError).toBeTruthy();

      const el: HTMLElement = fixture.nativeElement;
      const errEl = el.querySelector('[data-testid="server-error"]');
      expect(errEl).not.toBeNull();
      expect(errEl!.textContent!.trim().length).toBeGreaterThan(0);
    });

    it('should display a generic error message for a 422 error', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);
      fixture.detectChanges();

      const error422 = new HttpErrorResponse({ status: 422, statusText: 'Unprocessable Entity' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error422)
      );

      component.onChangePassword();
      await fixture.whenStable();

      expect(component.serverError).toBeTruthy();
    });

    it('should NOT expose raw server error details in the serverError message', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error500 = new HttpErrorResponse({
        status: 500,
        statusText: 'Internal Server Error',
        error: { detail: 'DB connection string xyz leaked here' },
      });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error500)
      );

      component.onChangePassword();
      await fixture.whenStable();

      expect(component.serverError).not.toContain('DB connection string');
      expect(component.serverError).not.toContain('xyz leaked here');
    });

    it('should set submitting back to false after a 500 error', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error500 = new HttpErrorResponse({ status: 500, statusText: 'Internal Server Error' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error500)
      );

      component.onChangePassword();
      await fixture.whenStable();

      expect(component.submitting).toBe(false);
    });

    it('should NOT set incorrectPassword error on current password field for a 500 error', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      fillValidForm(fixture);

      const error500 = new HttpErrorResponse({ status: 500, statusText: 'Internal Server Error' });
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        throwError(() => error500)
      );

      component.onChangePassword();
      await fixture.whenStable();

      const currentPwdControl = component.changePasswordForm.get('currentPassword');
      expect(currentPwdControl?.hasError('incorrectPassword')).toBe(false);
    });
  });

  // ─── No password logging or persistence (requirement 5.2) ─────────────────

  describe('password security (requirement 5.2)', () => {
    it('should not call console.log with any password value during submission', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      form.setValue({
        currentPassword: 'secretOld1',
        newPassword: 'secretNew1',
        confirmNewPassword: 'secretNew1',
      });

      const consoleSpy = vi.spyOn(console, 'log');
      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('new-token'));
      vi.spyOn(authStateService, 'setToken').mockImplementation(() => {});

      component.onChangePassword();

      const logCalls = consoleSpy.mock.calls.flat().join(' ');
      expect(logCalls).not.toContain('secretOld1');
      expect(logCalls).not.toContain('secretNew1');
    });

    it('should clear the form after success so no password values remain accessible', async () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;
      const form: FormGroup = component.changePasswordForm;
      form.setValue({
        currentPassword: 'oldPassword1',
        newPassword: 'newPassword1',
        confirmNewPassword: 'newPassword1',
      });
      // Stabilize before acting
      fixture.detectChanges();

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(of('new-token'));
      vi.spyOn(authStateService, 'setToken').mockImplementation(() => {});

      component.onChangePassword();
      await fixture.whenStable();

      // The FormGroup still exists but values are cleared
      expect(form.get('currentPassword')?.value).toBeFalsy();
      expect(form.get('newPassword')?.value).toBeFalsy();
      expect(form.get('confirmNewPassword')?.value).toBeFalsy();
    });
  });

  // ─── Success message cleared when submitting again ─────────────────────────

  describe('state cleanup across submissions', () => {
    it('should clear successMessage and serverError at the start of a new submission', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      // Simulate a previous success state
      component.successMessage = 'Password changed!';
      component.serverError = null;

      fillValidForm(fixture);

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        new Subject<string>().asObservable()
      );

      component.onChangePassword();

      // successMessage should be cleared when a new submission starts
      expect(component.successMessage).toBeNull();
    });

    it('should clear serverError at the start of a new submission', () => {
      const fixture = createComponent();
      const component = fixture.componentInstance as any;

      component.serverError = 'An unexpected error occurred. Please try again.';

      fillValidForm(fixture);

      vi.spyOn(authApiService, 'changePassword').mockReturnValue(
        new Subject<string>().asObservable()
      );

      component.onChangePassword();

      expect(component.serverError).toBeNull();
    });
  });
});
