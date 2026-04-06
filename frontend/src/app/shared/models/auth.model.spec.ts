import { describe, it, expect } from 'vitest';
import type { TokenResponse, ApiError, ValidationErrorDetail } from './auth.model';

describe('Auth model', () => {
  it('should allow a valid TokenResponse', () => {
    const token: TokenResponse = {
      access_token: 'eyJhbGciOiJIUzI1NiJ9.test.signature',
      token_type: 'bearer',
    };
    expect(token.access_token).toBe('eyJhbGciOiJIUzI1NiJ9.test.signature');
    expect(token.token_type).toBe('bearer');
  });

  it('should allow ApiError with a string detail', () => {
    const error: ApiError = { detail: 'Invalid credentials' };
    expect(error.detail).toBe('Invalid credentials');
  });

  it('should allow ApiError with an array of ValidationErrorDetail', () => {
    const details: ValidationErrorDetail[] = [
      { loc: ['body', 'email'], msg: 'Invalid email address', type: 'value_error' },
    ];
    const error: ApiError = { detail: details };
    expect(Array.isArray(error.detail)).toBe(true);
    const firstDetail = (error.detail as ValidationErrorDetail[])[0];
    expect(firstDetail.loc).toEqual(['body', 'email']);
    expect(firstDetail.msg).toBe('Invalid email address');
    expect(firstDetail.type).toBe('value_error');
  });
});
