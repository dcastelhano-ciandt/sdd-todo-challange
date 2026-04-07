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
    <div class="bg-surface text-on-surface antialiased min-h-screen flex flex-col">
      <main class="flex-grow flex items-center justify-center px-6 py-12 relative overflow-hidden">
        <!-- Background decorations -->
        <div
          class="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20 overflow-hidden"
        >
          <div
            class="absolute -top-24 -left-24 w-96 h-96 bg-primary-container rounded-full blur-[120px]"
          ></div>
          <div
            class="absolute -bottom-24 -right-24 w-96 h-96 bg-secondary-container rounded-full blur-[120px]"
          ></div>
        </div>

        <div class="w-full max-w-[400px] z-10">
          <!-- Header -->
          <div class="text-center mb-10">
            <div class="inline-flex items-center justify-center mb-6">
              <div
                class="w-12 h-12 bg-gradient-to-br from-primary to-primary-container rounded-xl flex items-center justify-center text-white shadow-xl"
              >
                <span
                  class="material-symbols-outlined text-3xl"
                  style="font-variation-settings: 'FILL' 1;"
                  >task_alt</span
                >
              </div>
            </div>
            <h1 class="text-3xl font-extrabold tracking-tighter text-on-surface mb-2">Task Flow</h1>
            <p class="text-on-surface-variant font-medium tracking-tight">
              Organize your day with ease
            </p>
          </div>

          <!-- Card -->
          <div
            class="bg-surface-container-lowest p-8 rounded-xl shadow-sm border border-outline-variant/15"
          >
            <form [formGroup]="form" (ngSubmit)="onSubmit()" class="space-y-6">
              <!-- Email -->
              <div class="space-y-2">
                <label class="block text-sm font-semibold text-on-surface-variant ml-1" for="email"
                  >Email address</label
                >
                <input
                  id="email"
                  type="email"
                  formControlName="email"
                  autocomplete="email"
                  placeholder="name@company.com"
                  class="w-full px-4 py-3 bg-surface-container-low border-0 rounded-xl focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all duration-200 outline-none text-on-surface placeholder:text-outline/50"
                />
                <span
                  *ngIf="form.get('email')?.touched && form.get('email')?.hasError('required')"
                  class="block text-xs text-error ml-1"
                >
                  Email is required.
                </span>
                <span
                  *ngIf="form.get('email')?.touched && form.get('email')?.hasError('email')"
                  class="block text-xs text-error ml-1"
                >
                  Please enter a valid email address.
                </span>
                <span
                  *ngIf="form.get('email')?.hasError('emailInUse')"
                  class="block text-xs text-error ml-1"
                >
                  This email address is already in use.
                </span>
              </div>

              <!-- Password -->
              <div class="space-y-2">
                <label
                  class="block text-sm font-semibold text-on-surface-variant ml-1"
                  for="password"
                  >Password</label
                >
                <div class="relative">
                  <input
                    id="password"
                    [type]="showPassword ? 'text' : 'password'"
                    formControlName="password"
                    autocomplete="new-password"
                    placeholder="••••••••"
                    class="w-full px-4 py-3 bg-surface-container-low border-0 rounded-xl focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all duration-200 outline-none text-on-surface placeholder:text-outline/50"
                  />
                  <button
                    type="button"
                    (click)="showPassword = !showPassword"
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-outline hover:text-primary transition-colors"
                  >
                    <span class="material-symbols-outlined text-xl">{{
                      showPassword ? 'visibility_off' : 'visibility'
                    }}</span>
                  </button>
                </div>
                <!-- Password strength indicator -->
                <div *ngIf="form.get('password')?.value" class="mt-3 px-1">
                  <div class="flex justify-between items-center mb-2">
                    <span
                      class="text-[10px] font-bold uppercase tracking-widest"
                      [ngClass]="passwordStrengthColor"
                      >Strength: {{ passwordStrengthLabel }}</span
                    >
                    <span class="text-[10px] text-on-surface-variant">8+ characters</span>
                  </div>
                  <div class="flex gap-1 h-1">
                    <div
                      class="flex-1 rounded-full"
                      [ngClass]="passwordStrength >= 1 ? 'bg-primary' : 'bg-surface-container-high'"
                    ></div>
                    <div
                      class="flex-1 rounded-full"
                      [ngClass]="passwordStrength >= 2 ? 'bg-primary' : 'bg-surface-container-high'"
                    ></div>
                    <div
                      class="flex-1 rounded-full"
                      [ngClass]="passwordStrength >= 3 ? 'bg-primary' : 'bg-surface-container-high'"
                    ></div>
                    <div
                      class="flex-1 rounded-full"
                      [ngClass]="passwordStrength >= 4 ? 'bg-primary' : 'bg-surface-container-high'"
                    ></div>
                  </div>
                </div>
                <span
                  *ngIf="
                    form.get('password')?.touched && form.get('password')?.hasError('required')
                  "
                  class="block text-xs text-error ml-1"
                >
                  Password is required.
                </span>
                <span
                  *ngIf="
                    form.get('password')?.touched && form.get('password')?.hasError('minlength')
                  "
                  class="block text-xs text-error ml-1"
                >
                  Password must be at least 8 characters.
                </span>
              </div>

              <!-- Server error -->
              <div
                *ngIf="serverError"
                class="flex items-center gap-2 bg-error-container/40 p-3 rounded-lg border border-error/10"
              >
                <span class="material-symbols-outlined text-error text-[18px]">error</span>
                <p class="text-sm font-medium text-on-error-container">{{ serverError }}</p>
              </div>

              <!-- Submit -->
              <button
                type="submit"
                [disabled]="form.invalid || submitting"
                class="w-full bg-gradient-to-br from-primary to-primary-container py-4 rounded-xl text-white font-bold tracking-tight shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {{ submitting ? 'Creating account...' : 'Create Account' }}
              </button>
            </form>
          </div>

          <!-- Bottom link -->
          <div class="mt-8 text-center">
            <p class="text-on-surface-variant text-sm font-medium">
              Already have an account?
              <a routerLink="/login" class="text-primary font-bold hover:underline ml-1">Sign in</a>
            </p>
          </div>
        </div>
      </main>
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
  showPassword = false;

  get passwordStrength(): number {
    const val: string = this.form.get('password')?.value ?? '';
    if (!val) return 0;
    let score = 0;
    if (val.length >= 8) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;
    return score;
  }

  get passwordStrengthLabel(): string {
    const s = this.passwordStrength;
    if (s <= 1) return 'Weak';
    if (s === 2) return 'Fair';
    if (s === 3) return 'Good';
    return 'Strong';
  }

  get passwordStrengthColor(): string {
    const s = this.passwordStrength;
    if (s <= 1) return 'text-error';
    if (s === 2) return 'text-[#d97706]';
    if (s === 3) return 'text-[#16a34a]';
    return 'text-primary';
  }

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
