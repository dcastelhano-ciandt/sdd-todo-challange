import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach } from 'vitest';
import { routes } from './app.routes';

describe('App routes', () => {
  it('should define a /login route', () => {
    const loginRoute = routes.find((r) => r.path === 'login');
    expect(loginRoute).toBeDefined();
  });

  it('should define a /register route', () => {
    const registerRoute = routes.find((r) => r.path === 'register');
    expect(registerRoute).toBeDefined();
  });

  it('should define a /tasks route', () => {
    const tasksRoute = routes.find((r) => r.path === 'tasks');
    expect(tasksRoute).toBeDefined();
  });

  it('should protect /tasks route with a canActivate guard', () => {
    const tasksRoute = routes.find((r) => r.path === 'tasks');
    expect(tasksRoute?.canActivate).toBeDefined();
    expect(tasksRoute?.canActivate?.length).toBeGreaterThan(0);
  });

  it('should have a redirect or wildcard route', () => {
    const redirectRoute = routes.find((r) => r.redirectTo || r.path === '**');
    expect(redirectRoute).toBeDefined();
  });

  // ─── Task 6: /dashboard route ────────────────────────────────────────────────

  it('should define a /dashboard route (requirement 1.1)', () => {
    const dashboardRoute = routes.find((r) => r.path === 'dashboard');
    expect(dashboardRoute).toBeDefined();
  });

  it('should protect /dashboard route with a canActivate guard (requirement 1.3)', () => {
    const dashboardRoute = routes.find((r) => r.path === 'dashboard');
    expect(dashboardRoute?.canActivate).toBeDefined();
    expect(dashboardRoute?.canActivate?.length).toBeGreaterThan(0);
  });

  it('should use the same authGuard on /dashboard as on /tasks (requirement 1.3)', () => {
    const tasksRoute = routes.find((r) => r.path === 'tasks');
    const dashboardRoute = routes.find((r) => r.path === 'dashboard');
    expect(tasksRoute?.canActivate).toBeDefined();
    expect(dashboardRoute?.canActivate).toBeDefined();
    // Both routes must be protected by the same guard function
    expect(dashboardRoute?.canActivate![0]).toBe(tasksRoute?.canActivate![0]);
  });

  it('should use lazy loading (loadComponent) for /dashboard route', () => {
    const dashboardRoute = routes.find((r) => r.path === 'dashboard');
    expect(typeof dashboardRoute?.loadComponent).toBe('function');
  });
});
