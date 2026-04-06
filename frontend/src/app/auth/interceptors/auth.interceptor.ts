import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthStateService } from '../services/auth-state.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authState = inject(AuthStateService);
  const router = inject(Router);

  const token = authState.getToken();
  const authReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authReq).pipe(
    catchError((err) => {
      const isAuthEndpoint = req.url.includes('/auth/');
      if (err instanceof HttpErrorResponse && err.status === 401 && !isAuthEndpoint) {
        authState.clearSession();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};
