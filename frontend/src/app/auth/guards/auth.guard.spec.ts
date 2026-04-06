import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, UrlTree } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { authGuard } from './auth.guard';
import { AuthStateService } from '../services/auth-state.service';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

function makeSnapshots(): { route: ActivatedRouteSnapshot; state: RouterStateSnapshot } {
  return {
    route: {} as ActivatedRouteSnapshot,
    state: { url: '/tasks', root: {} as ActivatedRouteSnapshot } as RouterStateSnapshot,
  };
}

describe('authGuard', () => {
  let authState: AuthStateService;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [provideRouter([])],
    });

    authState = TestBed.inject(AuthStateService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('when the user is authenticated', () => {
    it('should return true', () => {
      authState.setToken('valid-token');

      const { route, state } = makeSnapshots();
      const result = TestBed.runInInjectionContext(() => authGuard(route, state));

      expect(result).toBe(true);
    });
  });

  describe('when the user is not authenticated', () => {
    it('should return a UrlTree (redirect)', () => {
      const { route, state } = makeSnapshots();
      const result = TestBed.runInInjectionContext(() => authGuard(route, state));

      expect(result).toBeInstanceOf(UrlTree);
    });

    it('should redirect to /login', () => {
      const { route, state } = makeSnapshots();
      const result = TestBed.runInInjectionContext(() => authGuard(route, state));

      const urlTree = result as UrlTree;
      const serialized = router.serializeUrl(urlTree);
      expect(serialized).toBe('/login');
    });

    it('should deny access when clearSession was called after a token was set', () => {
      authState.setToken('some-token');
      authState.clearSession();

      const { route, state } = makeSnapshots();
      const result = TestBed.runInInjectionContext(() => authGuard(route, state));

      expect(result).toBeInstanceOf(UrlTree);
    });
  });
});
