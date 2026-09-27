import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  constructor(public auth: AuthService, private router: Router) {}

  logout() {
    this.auth.logout().subscribe({
      complete: () => {
        this.auth.loggedIn.set(false);
        this.router.navigate(['/login']);
      }
    });
  }
}
