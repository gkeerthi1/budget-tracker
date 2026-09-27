import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TransactionsService, Transaction } from '../../services/transactions.service';
import { CategoriesService, Category } from '../../services/categories.service';

@Component({
  selector: 'app-transactions',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h2>Transactions</h2>

    <form (ngSubmit)="addTransaction()" class="form-grid">
      <label>
        Type
        <select [(ngModel)]="type" name="type" data-testid="type-select">
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </label>
      <label>
        Amount
        <input type="number" [(ngModel)]="amount" name="amount" required data-testid="amount-input" />
      </label>
      <label *ngIf="type === 'expense'">
        Category
        <select [(ngModel)]="categoryId" name="categoryId" data-testid="category-select">
          <option [ngValue]="null">-- choose --</option>
          <option *ngFor="let c of categories" [ngValue]="c.id">{{ c.name }}</option>
        </select>
      </label>
      <label>
        Date
        <input type="date" [(ngModel)]="spentOn" name="spentOn" required data-testid="date-input" />
      </label>
      <label>
        Note
        <input type="text" [(ngModel)]="note" name="note" data-testid="note-input" />
      </label>
      <button type="submit" data-testid="add-transaction-btn">Add</button>
    </form>

    <p *ngIf="error" class="error" data-testid="transaction-error">{{ error }}</p>
    <p *ngIf="warning" class="warning" data-testid="budget-warning">{{ warning }}</p>

    <table *ngIf="transactions.length" data-testid="transaction-table">
      <thead>
        <tr><th>Date</th><th>Type</th><th>Amount</th><th>Note</th></tr>
      </thead>
      <tbody>
        <tr *ngFor="let t of transactions" [attr.data-testid]="'transaction-row-' + t.id">
          <td>{{ t.spent_on }}</td>
          <td>{{ t.type }}</td>
          <td>{{ t.amount }}</td>
          <td>{{ t.note }}</td>
        </tr>
      </tbody>
    </table>
    <p *ngIf="!transactions.length">No transactions yet.</p>
  `,
  styles: [`
    .form-grid { display: flex; gap: 10px; flex-wrap: wrap; align-items: end; margin-bottom: 16px; }
    label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
    input, select { padding: 6px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 14px; }
    .error { color: #b00020; }
    .warning { color: #b8860b; font-weight: bold; }
  `]
})
export class TransactionsComponent implements OnInit {
  transactions: Transaction[] = [];
  categories: Category[] = [];

  type: 'income' | 'expense' = 'expense';
  amount: number | null = null;
  categoryId: number | null = null;
  spentOn = new Date().toISOString().slice(0, 10);
  note = '';

  error = '';
  warning = '';

  constructor(
    private transactionsService: TransactionsService,
    private categoriesService: CategoriesService
  ) {}

  ngOnInit() {
    this.loadTransactions();
    this.categoriesService.list().subscribe({ next: (data) => (this.categories = data) });
  }

  loadTransactions() {
    this.transactionsService.list().subscribe({
      next: (data) => (this.transactions = data),
      error: () => (this.error = 'Could not load transactions.')
    });
  }

  addTransaction() {
    this.error = '';
    this.warning = '';
    if (this.amount === null) return;

    this.transactionsService.create({
      type: this.type,
      amount: this.amount,
      category_id: this.type === 'expense' ? this.categoryId : null,
      spent_on: this.spentOn,
      note: this.note
    }).subscribe({
      next: (res) => {
        if (res.budget_warning === 'over_budget' || res.overall_warning === 'over_budget') {
          this.warning = 'Over budget!';
        } else if (res.budget_warning === 'approaching_limit' || res.overall_warning === 'approaching_limit') {
          this.warning = 'Approaching your budget limit.';
        }
        this.amount = null;
        this.note = '';
        this.loadTransactions();
      },
      error: (err) => (this.error = err?.error?.error || 'Could not add transaction.')
    });
  }
}
