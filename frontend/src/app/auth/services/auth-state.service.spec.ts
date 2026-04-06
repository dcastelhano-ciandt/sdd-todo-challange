import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AuthStateService } from './auth-state.service';

const AUTH_TOKEN_KEY = 'auth_token';

describe('AuthStateService', () => {
  let service: AuthStateService;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthStateService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('initialization', () => {
    it('should initialize token as null when localStorage is empty', () => {
      expect(service.token()).toBeNull();
    });

    it('should initialize token from localStorage when a token is already stored', () => {
      localStorage.clear();
      const stored = 'pre-existing-token';
      localStorage.setItem(AUTH_TOKEN_KEY, stored);

      TestBed.resetTestingModule();
      TestBed.configureTestingModule({});
      const freshService = TestBed.inject(AuthStateService);

      expect(freshService.token()).toBe(stored);
    });

    it('should reflect isAuthenticated as false when no token in localStorage', () => {
      expect(service.isAuthenticated()).toBe(false);
    });

    it('should reflect isAuthenticated as true when a token is pre-loaded from localStorage', () => {
      localStorage.clear();
      localStorage.setItem(AUTH_TOKEN_KEY, 'some-token');

      TestBed.resetTestingModule();
      TestBed.configureTestingModule({});
      const freshService = TestBed.inject(AuthStateService);

      expect(freshService.isAuthenticated()).toBe(true);
    });
  });

  describe('setToken', () => {
    it('should update the token Signal', () => {
      const token = 'new-jwt-token';
      service.setToken(token);
      expect(service.token()).toBe(token);
    });

    it('should persist the token to localStorage', () => {
      const token = 'persisted-token';
      service.setToken(token);
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe(token);
    });

    it('should set isAuthenticated to true', () => {
      service.setToken('any-token');
      expect(service.isAuthenticated()).toBe(true);
    });

    it('should update getToken() to return the new token', () => {
      const token = 'retrieved-token';
      service.setToken(token);
      expect(service.getToken()).toBe(token);
    });
  });

  describe('clearSession', () => {
    it('should reset the token Signal to null', () => {
      service.setToken('some-token');
      service.clearSession();
      expect(service.token()).toBeNull();
    });

    it('should remove the token from localStorage', () => {
      service.setToken('some-token');
      service.clearSession();
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    });

    it('should set isAuthenticated to false', () => {
      service.setToken('some-token');
      service.clearSession();
      expect(service.isAuthenticated()).toBe(false);
    });

    it('should make getToken() return null', () => {
      service.setToken('some-token');
      service.clearSession();
      expect(service.getToken()).toBeNull();
    });
  });

  describe('getToken', () => {
    it('should return null when no token is set', () => {
      expect(service.getToken()).toBeNull();
    });

    it('should return the current token value', () => {
      service.setToken('token-value');
      expect(service.getToken()).toBe('token-value');
    });
  });
});
