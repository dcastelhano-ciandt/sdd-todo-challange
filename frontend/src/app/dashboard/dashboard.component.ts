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
    <div class="task-list-container">
      <div class="task-list-header">
        <h2>My Account</h2>
        <a routerLink="/tasks" data-testid="back-button" class="btn-logout">&larr; Back to Tasks</a>
      </div>

      <div class="dashboard-card">
        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            data-testid="email-input"
            type="email"
            [formControl]="emailControl"
            autocomplete="email"
          />
        </div>

        <div
          *ngIf="profileLoadError"
          class="server-error"
          data-testid="profile-load-error"
          role="alert"
        >
          {{ profileLoadError }}
        </div>
      </div>

      <div
        *ngIf="successMessage"
        class="success-message"
        data-testid="success-message"
        role="status"
      >
        {{ successMessage }}
      </div>

      <div class="dashboard-card">
        <h3>Change Password</h3>

        <form [formGroup]="changePasswordForm" (ngSubmit)="onChangePassword()">
          <div class="field">
            <label for="currentPassword">Current Password</label>
            <input
              id="currentPassword"
              type="password"
              formControlName="currentPassword"
              data-testid="current-password-input"
              autocomplete="current-password"
            />
            <span
              class="field-error"
              data-testid="current-password-required-error"
              *ngIf="
                changePasswordForm.get('currentPassword')?.touched &&
                changePasswordForm.get('currentPassword')?.hasError('required')
              "
            >
              Current password is required.
            </span>
            <span
              class="field-error"
              data-testid="current-password-incorrect-error"
              *ngIf="
                changePasswordForm.get('currentPassword')?.touched &&
                changePasswordForm.get('currentPassword')?.hasError('incorrectPassword')
              "
            >
              The current password you entered is incorrect.
            </span>
          </div>

          <div class="field">
            <label for="newPassword">New Password</label>
            <input
              id="newPassword"
              type="password"
              formControlName="newPassword"
              data-testid="new-password-input"
              autocomplete="new-password"
            />
            <span
              class="field-error"
              data-testid="new-password-required-error"
              *ngIf="
                changePasswordForm.get('newPassword')?.touched &&
                changePasswordForm.get('newPassword')?.hasError('required')
              "
            >
              New password is required.
            </span>
            <span
              class="field-error"
              data-testid="new-password-minlength-error"
              *ngIf="
                changePasswordForm.get('newPassword')?.touched &&
                changePasswordForm.get('newPassword')?.hasError('minlength')
              "
            >
              Password must be at least 8 characters.
            </span>
          </div>

          <div class="field">
            <label for="confirmNewPassword">Confirm New Password</label>
            <input
              id="confirmNewPassword"
              type="password"
              formControlName="confirmNewPassword"
              data-testid="confirm-password-input"
              autocomplete="new-password"
            />
            <span
              class="field-error"
              data-testid="confirm-password-required-error"
              *ngIf="
                changePasswordForm.get('confirmNewPassword')?.touched &&
                changePasswordForm.get('confirmNewPassword')?.hasError('required')
              "
            >
              Confirm new password is required.
            </span>
            <span
              class="field-error"
              data-testid="passwords-mismatch-error"
              *ngIf="
                changePasswordForm.get('confirmNewPassword')?.touched &&
                changePasswordForm.hasError('passwordsMismatch')
              "
            >
              New password and confirmation do not match.
            </span>
          </div>

          <button
            type="submit"
            class="btn-primary"
            [disabled]="changePasswordForm.invalid || submitting"
          >
            {{ submitting ? 'Changing password...' : 'Change Password' }}
          </button>

          <div *ngIf="serverError" class="server-error" data-testid="server-error" role="alert">
            {{ serverError }}
          </div>
        </form>
      </div>
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
  email: string | null = null;
  profileLoadError: string | null = null;
  submitting = false;
  successMessage: string | null = null;
  serverError: string | null = null;

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
        this.emailControl.setValue(profile.email);
        this.email = profile.email;
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
