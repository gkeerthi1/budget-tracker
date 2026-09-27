import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

@Injectable({ providedIn: 'root' })
export class AuthService {
  // Simple in-memory login flag. Good enough for the app + Playwright,
  // since Playwright always drives a real login flow from a fresh page.
  loggedIn = signal<boolean>(false);

  constructor(private http: HttpClient) {}

  register(email: string, password: string) {
    return this.http.post(`${API_BASE}/auth/register`, { email, password }, { withCredentials: true });
  }

  login(email: string, password: string) {
    return this.http.post(`${API_BASE}/auth/login`, { email, password }, { withCredentials: true });
  }

  logout() {
    return this.http.post(`${API_BASE}/auth/logout`, {}, { withCredentials: true });
  }
}
