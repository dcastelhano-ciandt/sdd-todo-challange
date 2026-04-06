import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormGroup,
  Validators,
} from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthApiService } from '../services/auth-api.service';
import { AuthStateService } from '../services/auth-state.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-container">
      <h2>Sign In</h2>

      <div class="session-expiry-notice" *ngIf="sessionExpired">
        Your session has expired. Please sign in again.
      </div>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            type="email"
            formControlName="email"
            autocomplete="email"
          />
          <span
            class="field-error"
            *ngIf="form.get('email')?.touched && form.get('email')?.hasError('required')"
          >
            Email is required.
          </span>
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            formControlName="password"
            autocomplete="current-password"
          />
          <span
            class="field-error"
            *ngIf="form.get('password')?.touched && form.get('password')?.hasError('required')"
          >
            Password is required.
          </span>
        </div>

        <div class="login-error" *ngIf="genericError" role="alert">
          <span class="login-error-icon">&#9888;</span>
          {{ genericError }}
        </div>

        <button type="submit" [disabled]="form.invalid || submitting">
          {{ submitting ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p>Don't have an account? <a routerLink="/register">Register</a></p>
    </div>
  `,
})
export class LoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly authState = inject(AuthStateService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  form: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  submitting = false;
  genericError: string | null = null;
  sessionExpired = false;

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      if (params.has('sessionExpired')) {
        this.sessionExpired = true;
      }
    });
  }

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }

    this.submitting = true;
    this.genericError = null;

    const { email, password } = this.form.value as { email: string; password: string };

    this.authApi.login(email, password).subscribe({
      next: (token: string) => {
        this.authState.setToken(token);
        this.router.navigate(['/tasks']);
      },
      error: (err: HttpErrorResponse) => {
        this.submitting = false;
        this.form.reset();
        if (err.status === 401) {
          this.genericError = 'Invalid email or password.';
        } else {
          this.genericError = 'An unexpected error occurred. Please try again.';
        }
      },
    });
  }
}
