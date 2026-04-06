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
});
