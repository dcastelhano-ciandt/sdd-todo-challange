import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { describe, it, expect, beforeEach } from 'vitest';
import { appConfig } from './app.config';

describe('App config', () => {
  beforeEach(async () => {
    TestBed.configureTestingModule({
      providers: [...appConfig.providers],
    });
    await TestBed.compileComponents();
  });

  it('should provide a Router', () => {
    const router = TestBed.inject(Router);
    expect(router).toBeTruthy();
  });

  it('should provide HttpClient', () => {
    const http = TestBed.inject(HttpClient);
    expect(http).toBeTruthy();
  });
});
