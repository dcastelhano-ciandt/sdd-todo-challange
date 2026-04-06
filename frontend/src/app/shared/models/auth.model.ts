export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  email: string;
}

export interface ValidationErrorDetail {
  loc: string[];
  msg: string;
  type: string;
}

export interface ApiError {
  detail: string | ValidationErrorDetail[];
}
