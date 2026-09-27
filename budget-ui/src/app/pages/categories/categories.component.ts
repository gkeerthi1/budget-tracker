import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CategoriesService, Category } from '../../services/categories.service';

@Component({
  selector: 'app-categories',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h2>Categories</h2>

    <form (ngSubmit)="addCategory()" class="inline-form">
      <input placeholder="Name" [(ngModel)]="newName" name="newName" required data-testid="category-name-input" />
      <input placeholder="Monthly budget" type="number" [(ngModel)]="newBudget" name="newBudget" required data-testid="category-budget-input" />
      <button type="submit" data-testid="add-category-btn">Add category</button>
    </form>
    <p *ngIf="error" class="error" data-testid="category-error">{{ error }}</p>

    <table *ngIf="categories.length" data-testid="category-table">
      <thead>
        <tr>
          <th>Name</th><th>Budget</th><th>Rollover</th><th>Effective</th><th>Spent</th><th>Remaining</th><th>Status</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let c of categories" [attr.data-testid]="'category-row-' + c.id">
          <td>{{ c.name }}</td>
          <td>{{ c.monthly_budget }}</td>
          <td>{{ c.rollover_amount }}</td>
          <td>{{ c.effective_budget }}</td>
          <td>{{ c.spent_this_month }}</td>
          <td>{{ c.remaining_balance }}</td>
          <td [class]="'status-' + (c.status || 'ok')">{{ c.status || 'ok' }}</td>
          <td><button (click)="deleteCategory(c.id)" data-testid="delete-category-btn">Delete</button></td>
        </tr>
      </tbody>
    </table>
    <p *ngIf="!categories.length">No categories yet.</p>
  `,
  styles: [`
    .inline-form { display: flex; gap: 8px; margin-bottom: 16px; }
    input { padding: 6px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 14px; }
    .status-approaching_limit { color: #b8860b; font-weight: bold; }
    .status-over_budget { color: #b00020; font-weight: bold; }
    .error { color: #b00020; }
  `]
})
export class CategoriesComponent implements OnInit {
  categories: Category[] = [];
  newName = '';
  newBudget: number | null = null;
  error = '';

  constructor(private categoriesService: CategoriesService) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.categoriesService.list().subscribe({
      next: (data) => (this.categories = data),
      error: () => (this.error = 'Could not load categories.')
    });
  }

  addCategory() {
    this.error = '';
    if (this.newBudget === null) return;
    this.categoriesService.create(this.newName, this.newBudget).subscribe({
      next: () => {
        this.newName = '';
        this.newBudget = null;
        this.load();
      },
      error: (err) => (this.error = err?.error?.error || 'Could not add category.')
    });
  }

  deleteCategory(id: number) {
    this.categoriesService.delete(id).subscribe({
      next: () => this.load(),
      error: () => (this.error = 'Could not delete category.')
    });
  }
}
