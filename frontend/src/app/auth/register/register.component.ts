import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthApiService } from '../services/auth-api.service';
import { AuthStateService } from '../services/auth-state.service';
import { ValidationErrorDetail } from '../../shared/models/auth.model';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-container">
      <h2>Create Account</h2>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="field">
          <label for="email">Email</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
          <span
            class="field-error"
            *ngIf="form.get('email')?.touched && form.get('email')?.hasError('required')"
          >
            Email is required.
          </span>
          <span
            class="field-error"
            *ngIf="form.get('email')?.touched && form.get('email')?.hasError('email')"
          >
            Please enter a valid email address.
          </span>
          <span class="field-error" *ngIf="form.get('email')?.hasError('emailInUse')">
            This email address is already in use.
          </span>
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            formControlName="password"
            autocomplete="new-password"
          />
          <span
            class="field-error"
            *ngIf="form.get('password')?.touched && form.get('password')?.hasError('required')"
          >
            Password is required.
          </span>
          <span
            class="field-error"
            *ngIf="form.get('password')?.touched && form.get('password')?.hasError('minlength')"
          >
            Password must be at least 8 characters.
          </span>
        </div>

        <div class="server-error" *ngIf="serverError">
          {{ serverError }}
        </div>

        <button type="submit" [disabled]="form.invalid || submitting">
          {{ submitting ? 'Registering...' : 'Register' }}
        </button>
      </form>

      <p>Already have an account? <a routerLink="/login">Sign in</a></p>
    </div>
  `,
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly authState = inject(AuthStateService);
  private readonly router = inject(Router);

  form: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submitting = false;
  serverError: string | null = null;

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }

    this.submitting = true;
    this.serverError = null;

    const { email, password } = this.form.value as { email: string; password: string };

    this.authApi.register(email, password).subscribe({
      next: (token: string) => {
        this.authState.setToken(token);
        this.router.navigate(['/tasks']);
      },
      error: (err: HttpErrorResponse) => {
        this.submitting = false;
        if (err.status === 409) {
          this.form.get('email')?.setErrors({ emailInUse: true });
        } else if (err.status === 422) {
          const detail = err.error?.detail;
          if (Array.isArray(detail)) {
            const messages = (detail as ValidationErrorDetail[]).map((d) => d.msg).join(', ');
            this.serverError = messages;
          } else {
            this.serverError = 'Validation error. Please check your input.';
          }
        } else {
          this.serverError = 'An unexpected error occurred. Please try again.';
        }
      },
    });
  }
}
