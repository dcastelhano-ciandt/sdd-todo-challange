import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthApiService } from '../services/auth-api.service';
import { AuthStateService } from '../services/auth-state.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="bg-surface text-on-background antialiased flex items-center justify-center min-h-screen p-6">
      <!-- Background decoration -->
      <div class="fixed top-0 right-0 -z-10 w-[40vw] h-[40vw] bg-primary-fixed/30 rounded-full blur-[120px] translate-x-1/2 -translate-y-1/2"></div>
      <div class="fixed bottom-0 left-0 -z-10 w-[30vw] h-[30vw] bg-surface-container-high/50 rounded-full blur-[100px] -translate-x-1/2 translate-y-1/2"></div>

      <main class="w-full max-w-[400px] flex flex-col gap-8">
        <!-- Brand -->
        <header class="flex flex-col items-center text-center space-y-2">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-container flex items-center justify-center shadow-lg shadow-primary/20">
              <span class="material-symbols-outlined text-white" style="font-variation-settings: 'FILL' 1;">task_alt</span>
            </div>
            <h1 class="text-2xl font-extrabold tracking-tighter text-on-surface">Task Flow</h1>
          </div>
          <p class="text-on-surface-variant font-medium tracking-tight">Organize your day with ease</p>
        </header>

        <!-- Card -->
        <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0_24px_48px_-12px_rgba(19,27,46,0.04)] border border-outline-variant/15">
          <!-- Session expiry notice -->
          <div *ngIf="sessionExpired" class="flex items-center gap-2 bg-[#fffbeb] p-3 rounded-lg border border-[#fde68a] mb-6">
            <span class="material-symbols-outlined text-[#d97706] text-[18px]">warning</span>
            <p class="text-sm font-medium text-[#92400e]">Your session has expired. Please sign in again.</p>
          </div>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="space-y-6">
            <!-- Email -->
            <div class="space-y-2">
              <label class="block text-sm font-semibold text-on-surface-variant px-1" for="email">Email</label>
              <input
                id="email"
                type="email"
                formControlName="email"
                autocomplete="email"
                placeholder="name@company.com"
                class="w-full px-4 py-3 bg-surface-container-low border-0 rounded-xl focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all duration-200 outline-none text-on-surface"
              />
              <span *ngIf="form.get('email')?.touched && form.get('email')?.hasError('required')" class="block text-xs text-error px-1">
                Email is required.
              </span>
            </div>

            <!-- Password -->
            <div class="space-y-2">
              <div class="flex justify-between items-center px-1">
                <label class="block text-sm font-semibold text-on-surface-variant" for="password">Password</label>
              </div>
              <div class="relative">
                <input
                  id="password"
                  [type]="showPassword ? 'text' : 'password'"
                  formControlName="password"
                  autocomplete="current-password"
                  placeholder="••••••••"
                  class="w-full px-4 py-3 bg-surface-container-low border-0 rounded-xl focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all duration-200 outline-none text-on-surface"
                />
                <button type="button" (click)="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface">
                  <span class="material-symbols-outlined text-[20px]">{{ showPassword ? 'visibility' : 'visibility_off' }}</span>
                </button>
              </div>
              <span *ngIf="form.get('password')?.touched && form.get('password')?.hasError('required')" class="block text-xs text-error px-1">
                Password is required.
              </span>
            </div>

            <!-- Error -->
            <div *ngIf="genericError" role="alert" class="flex items-center gap-2 bg-error-container/40 p-3 rounded-lg border border-error/10">
              <span class="material-symbols-outlined text-error text-[18px]">error</span>
              <p class="text-sm font-medium text-on-error-container">{{ genericError }}</p>
            </div>

            <!-- Submit -->
            <button
              type="submit"
              [disabled]="form.invalid || submitting"
              class="w-full py-3.5 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-xl shadow-md shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ submitting ? 'Signing in...' : 'Sign In' }}
            </button>
          </form>

          <div class="mt-8 pt-6 border-t border-outline-variant/10 text-center">
            <p class="text-on-surface-variant text-sm">
              Don't have an account?
              <a routerLink="/register" class="font-bold text-primary hover:text-primary-container transition-colors ml-1">Register</a>
            </p>
          </div>
        </div>

        <footer class="text-center">
          <div class="flex justify-center gap-4">
            <div class="h-1 w-1 rounded-full bg-outline-variant"></div>
            <div class="h-1 w-1 rounded-full bg-outline-variant"></div>
            <div class="h-1 w-1 rounded-full bg-outline-variant"></div>
          </div>
        </footer>
      </main>
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
  showGenericError = false;
  sessionExpired = false;
  showPassword = false;

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
        // Do not reset the whole form to avoid setting required errors; just clear password field.
        this.form.get('password')?.setValue('');
        this.form.get('password')?.markAsPristine();
        this.form.get('password')?.markAsUntouched();
        this.form.get('password')?.setErrors(null);
        // Set message immediately for tests; toggle visibility next macrotask to avoid NG0100 in template.
        if (err.status === 401) {
          this.genericError = 'Invalid email or password.';
        } else {
          this.genericError = 'An unexpected error occurred. Please try again.';
        }
        setTimeout(() => {
          this.showGenericError = true;
        });
      },
    });
  }
}
