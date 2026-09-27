import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RecurringService, RecurringRule } from '../../services/recurring.service';
import { CategoriesService, Category } from '../../services/categories.service';

@Component({
  selector: 'app-recurring',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h2>Recurring Transactions</h2>
    <p class="hint">
      Rules here run automatically each month on the day you set — e.g. Salary on the 1st,
      Rent on the 1st. They get generated the next time you log in on or after that day.
    </p>

    <form (ngSubmit)="addRule()" class="form-grid">
      <label>
        Type
        <select [(ngModel)]="type" name="type" data-testid="recurring-type-select">
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </label>
      <label>
        Amount
        <input type="number" [(ngModel)]="amount" name="amount" required data-testid="recurring-amount-input" />
      </label>
      <label *ngIf="type === 'expense'">
        Category
        <select [(ngModel)]="categoryId" name="categoryId" data-testid="recurring-category-select">
          <option [ngValue]="null">-- choose --</option>
          <option *ngFor="let c of categories" [ngValue]="c.id">{{ c.name }}</option>
        </select>
      </label>
      <label>
        Day of month
        <input type="number" min="1" max="28" [(ngModel)]="dayOfMonth" name="dayOfMonth" required data-testid="recurring-day-input" />
      </label>
      <label>
        Note
        <input type="text" [(ngModel)]="note" name="note" data-testid="recurring-note-input" />
      </label>
      <button type="submit" data-testid="add-recurring-btn">Add rule</button>
    </form>

    <p *ngIf="error" class="error" data-testid="recurring-error">{{ error }}</p>

    <table *ngIf="rules.length" data-testid="recurring-table">
      <thead>
        <tr><th>Type</th><th>Amount</th><th>Day of month</th><th>Note</th><th></th></tr>
      </thead>
      <tbody>
        <tr *ngFor="let r of rules" [attr.data-testid]="'recurring-row-' + r.id">
          <td>{{ r.type }}</td>
          <td>{{ r.amount }}</td>
          <td>{{ r.day_of_month }}</td>
          <td>{{ r.note }}</td>
          <td><button (click)="deleteRule(r.id)" data-testid="delete-recurring-btn">Delete</button></td>
        </tr>
      </tbody>
    </table>
    <p *ngIf="!rules.length">No recurring rules yet.</p>
  `,
  styles: [`
    .hint { color: #555; font-size: 13px; max-width: 520px; margin-bottom: 16px; }
    .form-grid { display: flex; gap: 10px; flex-wrap: wrap; align-items: end; margin-bottom: 16px; }
    label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
    input, select { padding: 6px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 14px; }
    .error { color: #b00020; }
  `]
})
export class RecurringComponent implements OnInit {
  rules: RecurringRule[] = [];
  categories: Category[] = [];

  type: 'income' | 'expense' = 'income';
  amount: number | null = null;
  categoryId: number | null = null;
  dayOfMonth: number | null = 1;
  note = '';
  error = '';

  constructor(
    private recurringService: RecurringService,
    private categoriesService: CategoriesService
  ) {}

  ngOnInit() {
    this.load();
    this.categoriesService.list().subscribe({ next: (data) => (this.categories = data) });
  }

  load() {
    this.recurringService.list().subscribe({
      next: (data) => (this.rules = data),
      error: () => (this.error = 'Could not load recurring rules.')
    });
  }

  addRule() {
    this.error = '';
    if (this.amount === null || this.dayOfMonth === null) return;

    this.recurringService.create({
      type: this.type,
      amount: this.amount,
      day_of_month: this.dayOfMonth,
      category_id: this.type === 'expense' ? this.categoryId : null,
      note: this.note
    }).subscribe({
      next: () => {
        this.amount = null;
        this.note = '';
        this.load();
      },
      error: (err) => (this.error = err?.error?.error || 'Could not add rule.')
    });
  }

  deleteRule(id: number) {
    this.recurringService.delete(id).subscribe({
      next: () => this.load(),
      error: () => (this.error = 'Could not delete rule.')
    });
  }
}
