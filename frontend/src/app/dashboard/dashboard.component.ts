import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormControl,
  FormGroup,
  Validators,
  AbstractControl,
  ValidationErrors,
} from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { AuthApiService } from '../auth/services/auth-api.service';
import { AuthStateService } from '../auth/services/auth-state.service';

export function passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
  const newPassword = control.get('newPassword');
  const confirmNewPassword = control.get('confirmNewPassword');

  if (!newPassword || !confirmNewPassword) {
    return null;
  }

  if (newPassword.value !== confirmNewPassword.value) {
    return { passwordsMismatch: true };
  }

  return null;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="bg-surface text-on-surface min-h-screen">
      <!-- Top Navigation -->
      <header class="w-full top-0 sticky z-40 bg-surface border-b border-outline-variant/20">
        <nav class="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto">
          <div class="flex items-center gap-8">
            <span class="text-xl font-bold tracking-tighter text-primary">Task Flow</span>
            <div class="hidden md:flex items-center gap-6">
              <a
                routerLink="/tasks"
                class="text-on-surface-variant hover:text-primary py-5 text-sm transition-colors"
                >Tasks</a
              >
              <a class="text-primary font-semibold border-b-2 border-primary py-5 text-sm" href="#"
                >Account</a
              >
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="p-2 hover:bg-surface-container-low rounded-full transition-colors"
            >
              <span class="material-symbols-outlined text-on-surface-variant text-[22px]"
                >notifications</span
              >
            </button>
            <div
              class="w-8 h-8 bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs ring-2 ring-primary/20"
              style="border-radius: 9999px"
            >
              {{ initials }}
            </div>
          </div>
        </nav>
      </header>

      <main class="max-w-[800px] mx-auto px-6 py-12">
        <header class="mb-12">
          <h1 class="text-3xl font-extrabold tracking-tighter text-on-surface mb-2">
            Account Settings
          </h1>
          <p class="text-on-surface-variant text-sm">
            Manage your profile, security, and preferences.
          </p>
        </header>

        <!-- Success feedback -->
        <div
          *ngIf="successMessage"
          data-testid="success-message"
          role="status"
          class="mb-8 flex items-center gap-3 bg-indigo-50 border border-indigo-100 p-4 rounded-xl text-indigo-700"
        >
          <span class="material-symbols-outlined text-indigo-600">check_circle</span>
          <span class="font-medium text-sm">{{ successMessage }}</span>
        </div>

        <div class="space-y-12">
          <!-- Profile Identity -->
          <section
            class="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-outline-variant/10"
          >
            <div>
              <h2 class="text-base font-bold tracking-tight text-on-surface">Profile Identity</h2>
              <p class="text-sm text-on-surface-variant mt-1">
                This information is visible within your workspace.
              </p>
            </div>
            <div class="md:col-span-2 flex items-center gap-6">
              <div
                class="w-20 h-20 flex-shrink-0 bg-gradient-to-br from-primary to-primary-container flex items-center justify-center text-white text-2xl font-bold ring-2 ring-primary/20"
                style="border-radius: 9999px"
              >
                {{ initials }}
              </div>
              <div>
                <div class="text-lg font-semibold text-on-surface">{{ displayName }}</div>
                <div class="text-sm text-on-surface-variant mt-0.5">{{ email }}</div>
                <div
                  *ngIf="profileLoadError"
                  class="text-xs text-error mt-1"
                  data-testid="profile-load-error"
                >
                  {{ profileLoadError }}
                </div>
              </div>
            </div>
          </section>

          <!-- Security -->
          <section
            class="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-outline-variant/10"
          >
            <div>
              <h2 class="text-base font-bold tracking-tight text-on-surface">Security</h2>
              <p class="text-sm text-on-surface-variant mt-1">
                Ensure your account is using a long, random password.
              </p>
            </div>
            <div class="md:col-span-2 space-y-6">
              <form
                [formGroup]="changePasswordForm"
                (ngSubmit)="onChangePassword()"
                class="space-y-4"
              >
                <div>
                  <label
                    class="block text-sm font-medium text-on-surface mb-2"
                    for="currentPassword"
                    >Current Password</label
                  >
                  <input
                    id="currentPassword"
                    type="password"
                    formControlName="currentPassword"
                    data-testid="current-password-input"
                    autocomplete="current-password"
                    class="w-full bg-surface-container-low border-none rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all outline-none"
                  />
                  <span
                    class="block text-xs text-error mt-1"
                    data-testid="current-password-required-error"
                    *ngIf="
                      changePasswordForm.get('currentPassword')?.touched &&
                      changePasswordForm.get('currentPassword')?.hasError('required')
                    "
                  >
                    Current password is required.
                  </span>
                  <span
                    class="block text-xs text-error mt-1"
                    data-testid="current-password-incorrect-error"
                    *ngIf="
                      changePasswordForm.get('currentPassword')?.touched &&
                      changePasswordForm.get('currentPassword')?.hasError('incorrectPassword')
                    "
                  >
                    The current password you entered is incorrect.
                  </span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-on-surface mb-2" for="newPassword"
                      >New Password</label
                    >
                    <input
                      id="newPassword"
                      type="password"
                      formControlName="newPassword"
                      data-testid="new-password-input"
                      autocomplete="new-password"
                      placeholder="Min. 8 characters"
                      class="w-full bg-surface-container-low border-none rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all outline-none placeholder:text-outline/50"
                    />
                    <span
                      class="block text-xs text-error mt-1"
                      data-testid="new-password-required-error"
                      *ngIf="
                        changePasswordForm.get('newPassword')?.touched &&
                        changePasswordForm.get('newPassword')?.hasError('required')
                      "
                    >
                      New password is required.
                    </span>
                    <span
                      class="block text-xs text-error mt-1"
                      data-testid="new-password-minlength-error"
                      *ngIf="
                        changePasswordForm.get('newPassword')?.touched &&
                        changePasswordForm.get('newPassword')?.hasError('minlength')
                      "
                    >
                      Password must be at least 8 characters.
                    </span>
                  </div>
                  <div>
                    <label
                      class="block text-sm font-medium text-on-surface mb-2"
                      for="confirmNewPassword"
                      >Confirm New Password</label
                    >
                    <input
                      id="confirmNewPassword"
                      type="password"
                      formControlName="confirmNewPassword"
                      data-testid="confirm-password-input"
                      autocomplete="new-password"
                      placeholder="Repeat password"
                      class="w-full bg-surface-container-low border-none rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all outline-none placeholder:text-outline/50"
                    />
                    <span
                      class="block text-xs text-error mt-1"
                      data-testid="confirm-password-required-error"
                      *ngIf="
                        changePasswordForm.get('confirmNewPassword')?.touched &&
                        changePasswordForm.get('confirmNewPassword')?.hasError('required')
                      "
                    >
                      Confirm new password is required.
                    </span>
                    <span
                      class="block text-xs text-error mt-1"
                      data-testid="passwords-mismatch-error"
                      *ngIf="
                        changePasswordForm.get('confirmNewPassword')?.touched &&
                        changePasswordForm.hasError('passwordsMismatch')
                      "
                    >
                      New password and confirmation do not match.
                    </span>
                  </div>
                </div>

                <div
                  *ngIf="serverError"
                  class="flex items-center gap-2 bg-error-container/40 p-3 rounded-lg border border-error/10"
                  data-testid="server-error"
                  role="alert"
                >
                  <span class="material-symbols-outlined text-error text-[18px]">error</span>
                  <p class="text-sm font-medium text-on-error-container">{{ serverError }}</p>
                </div>

                <div class="flex justify-end">
                  <button
                    type="submit"
                    [disabled]="changePasswordForm.invalid || submitting"
                    class="bg-gradient-to-br from-primary to-primary-container text-white px-6 py-2.5 rounded-xl font-semibold text-sm shadow-sm hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ submitting ? 'Updating...' : 'Update Password' }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <!-- Danger Zone -->
          <section class="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12">
            <div>
              <h2 class="text-base font-bold tracking-tight text-error">Danger Zone</h2>
              <p class="text-sm text-on-surface-variant mt-1">
                Irreversible actions that affect your data.
              </p>
            </div>
            <div class="md:col-span-2">
              <div
                class="bg-error-container/30 border border-error/10 p-6 rounded-xl flex items-center justify-between gap-4"
              >
                <div>
                  <h3 class="font-bold text-on-error-container text-sm">Delete Account</h3>
                  <p class="text-sm text-on-error-container/80 mt-1">
                    Permanently delete your tasks and workspace.
                  </p>
                </div>
                <button
                  type="button"
                  class="text-error font-semibold text-sm px-4 py-2 hover:bg-error/5 rounded-xl transition-colors flex-shrink-0"
                >
                  Delete Account
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly authState = inject(AuthStateService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  emailControl = new FormControl({ value: '', disabled: true });
  profileLoadError: string | null = null;
  submitting = false;
  successMessage: string | null = null;
  serverError: string | null = null;
  initials = '';
  displayName = '';
  email = '';

  changePasswordForm: FormGroup = this.fb.group(
    {
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmNewPassword: ['', [Validators.required, Validators.minLength(8)]],
    },
    { validators: passwordsMatchValidator },
  );

  ngOnInit(): void {
    this.authApi.getProfile().subscribe({
      next: (profile) => {
        this.email = profile.email;
        this.emailControl.setValue(profile.email);
        const local = profile.email.split('@')[0];
        this.initials = local[0].toUpperCase();
        this.displayName = local.charAt(0).toUpperCase() + local.slice(1);
        this.cdr.detectChanges();
      },
      error: (_err: HttpErrorResponse) => {
        this.profileLoadError =
          'Unable to load your profile. Please refresh the page or try again later.';
      },
    });
  }

  onChangePassword(): void {
    if (this.changePasswordForm.invalid) {
      return;
    }

    this.submitting = true;
    this.successMessage = null;
    this.serverError = null;

    const currentPassword: string = this.changePasswordForm.get('currentPassword')!.value;
    const newPassword: string = this.changePasswordForm.get('newPassword')!.value;

    this.authApi.changePassword(currentPassword, newPassword).subscribe({
      next: (newToken: string) => {
        this.authState.setToken(newToken);
        this.changePasswordForm.reset();
        this.successMessage = 'Password changed successfully.';
        this.submitting = false;
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 401) {
          this.changePasswordForm.get('currentPassword')!.setErrors({ incorrectPassword: true });
          this.changePasswordForm.get('currentPassword')!.markAsTouched();
        } else {
          this.serverError = 'An unexpected error occurred. Please try again.';
        }
        this.submitting = false;
      },
    });
  }
}
