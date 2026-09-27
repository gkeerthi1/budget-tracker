import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-box">
      <h2>{{ mode === 'login' ? 'Log in' : 'Create account' }}</h2>

      <form (ngSubmit)="submit()">
        <label>
          Email
          <input type="email" name="email" [(ngModel)]="email" required data-testid="email-input" />
        </label>
        <label>
          Password
          <input type="password" name="password" [(ngModel)]="password" required data-testid="password-input" />
        </label>
        <button type="submit" data-testid="submit-btn">
          {{ mode === 'login' ? 'Log in' : 'Register' }}
        </button>
      </form>

      <p *ngIf="error" class="error" data-testid="auth-error">{{ error }}</p>

      <p>
        <a href="javascript:void(0)" (click)="toggleMode()" data-testid="toggle-mode">
          {{ mode === 'login' ? 'Need an account? Register' : 'Already have an account? Log in' }}
        </a>
      </p>
    </div>
  `,
  styles: [`
    .auth-box { max-width: 320px; margin: 60px auto; display: flex; flex-direction: column; gap: 12px; }
    form { display: flex; flex-direction: column; gap: 10px; }
    label { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
    input { padding: 8px; font-size: 14px; }
    button { padding: 8px; cursor: pointer; }
    .error { color: #b00020; }
  `]
})
export class LoginComponent {
  mode: 'login' | 'register' = 'login';
  email = '';
  password = '';
  error = '';

  constructor(private auth: AuthService, private router: Router) {}

  toggleMode() {
    this.mode = this.mode === 'login' ? 'register' : 'login';
    this.error = '';
  }

  submit() {
    this.error = '';
    const action = this.mode === 'login'
      ? this.auth.login(this.email, this.password)
      : this.auth.register(this.email, this.password);

    action.subscribe({
      next: () => {
        if (this.mode === 'register') {
          // Backend registers but doesn't auto-login; log in right after.
          this.auth.login(this.email, this.password).subscribe({
            next: () => this.afterLogin(),
            error: () => (this.error = 'Registered, but login failed. Try logging in.')
          });
        } else {
          this.afterLogin();
        }
      },
      error: (err) => {
        this.error = err?.error?.error || err?.error?.message || 'Something went wrong.';
      }
    });
  }

  private afterLogin() {
    this.auth.loggedIn.set(true);
    this.router.navigate(['/dashboard']);
  }
}
