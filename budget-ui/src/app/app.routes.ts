import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { CategoriesComponent } from './pages/categories/categories.component';
import { TransactionsComponent } from './pages/transactions/transactions.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { RecurringComponent } from './pages/recurring/recurring.component';
import { GoalsComponent } from './pages/goals/goals.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'categories', component: CategoriesComponent, canActivate: [authGuard] },
  { path: 'transactions', component: TransactionsComponent, canActivate: [authGuard] },
  { path: 'recurring', component: RecurringComponent, canActivate: [authGuard] },
  { path: 'goals', component: GoalsComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'login' }
];
