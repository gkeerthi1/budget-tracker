import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService, DashboardSummary, MonthEntry } from '../../services/dashboard.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h2>Dashboard</h2>

    <div *ngIf="summary" class="totals" data-testid="dashboard-totals">
      <div>Income: <strong data-testid="total-income">{{ summary.total_income }}</strong></div>
      <div>Expenses: <strong data-testid="total-expenses">{{ summary.total_expenses }}</strong></div>
      <div>Net: <strong data-testid="net-total">{{ summary.balance }}</strong></div>
    </div>

    <table *ngIf="summary?.categories?.length" data-testid="dashboard-category-table">
      <thead>
        <tr><th>Category</th><th>Budget</th><th>Spent</th><th>Remaining</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr *ngFor="let c of summary!.categories" [attr.data-testid]="'dashboard-row-' + c.id">
          <td>{{ c.name }}</td>
          <td>{{ c.effective_budget }}</td>
          <td>{{ c.spent_this_month }}</td>
          <td>{{ c.remaining_balance }}</td>
          <td [class]="'status-' + (c.status || 'ok')">{{ c.status || 'ok' }}</td>
        </tr>
      </tbody>
    </table>

    <p *ngIf="error" class="error">{{ error }}</p>

    <hr />

    <h2>Month-to-Month Comparison</h2>

    <label class="months-picker">
      Months to show
      <select [(ngModel)]="monthsToShow" (ngModelChange)="loadCompare()" data-testid="months-select">
        <option [ngValue]="3">3</option>
        <option [ngValue]="6">6</option>
        <option [ngValue]="12">12</option>
      </select>
    </label>

    <div *ngIf="compareMonths.length" class="chart" data-testid="compare-chart">
      <div class="chart-bar-group" *ngFor="let m of compareMonths" [attr.data-testid]="'compare-month-' + m.month">
        <div class="bars">
          <div class="bar income" [style.height.px]="scaledHeight(m.total_income)" [title]="'Income: ' + m.total_income"></div>
          <div class="bar expense" [style.height.px]="scaledHeight(m.total_expenses)" [title]="'Expenses: ' + m.total_expenses"></div>
        </div>
        <div class="month-label">{{ m.month }}</div>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="swatch income"></span> Income</span>
      <span class="legend-item"><span class="swatch expense"></span> Expenses</span>
    </div>

    <table *ngIf="compareMonths.length" data-testid="compare-table">
      <thead>
        <tr><th>Month</th><th>Income</th><th>Expenses</th><th>Net</th></tr>
      </thead>
      <tbody>
        <tr *ngFor="let m of compareMonths" [attr.data-testid]="'compare-row-' + m.month">
          <td>{{ m.month }}</td>
          <td>{{ m.total_income }}</td>
          <td>{{ m.total_expenses }}</td>
          <td>{{ m.total_income - m.total_expenses }}</td>
        </tr>
      </tbody>
    </table>

    <h3 *ngIf="compareMonths.length">Per-category trend</h3>
    <table *ngIf="compareMonths.length" data-testid="compare-category-table">
      <thead>
        <tr>
          <th>Category</th>
          <th *ngFor="let m of compareMonths">{{ m.month }}</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let name of categoryNames">
          <td>{{ name }}</td>
          <td *ngFor="let m of compareMonths" [class]="'status-' + (statusFor(m, name) || 'ok')">
            {{ spentFor(m, name) }}
          </td>
        </tr>
      </tbody>
    </table>

    <p *ngIf="compareError" class="error">{{ compareError }}</p>
  `,
  styles: [`
    .totals { display: flex; gap: 24px; margin-bottom: 20px; font-size: 15px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 14px; }
    .status-approaching_limit { color: #b8860b; font-weight: bold; }
    .status-over_budget { color: #b00020; font-weight: bold; }
    .error { color: #b00020; }
    hr { margin: 32px 0; border: none; border-top: 1px solid #ddd; }
    .months-picker { display: flex; gap: 8px; align-items: center; font-size: 14px; margin-bottom: 16px; }

    .chart {
      display: flex;
      align-items: flex-end;
      gap: 20px;
      height: 180px;
      padding: 10px 0;
      border-bottom: 2px solid #333;
      margin-bottom: 8px;
    }
    .chart-bar-group { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .bars { display: flex; align-items: flex-end; gap: 4px; height: 150px; }
    .bar { width: 18px; border-radius: 2px 2px 0 0; min-height: 2px; }
    .bar.income { background: #2e7d32; }
    .bar.expense { background: #b00020; }
    .month-label { font-size: 12px; color: #555; }

    .legend { display: flex; gap: 16px; margin-bottom: 20px; font-size: 13px; }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .swatch { width: 12px; height: 12px; display: inline-block; border-radius: 2px; }
    .swatch.income { background: #2e7d32; }
    .swatch.expense { background: #b00020; }
  `]
})
export class DashboardComponent implements OnInit {
  summary: DashboardSummary | null = null;
  error = '';

  compareMonths: MonthEntry[] = [];
  compareError = '';
  monthsToShow = 6;
  private maxValue = 1;

  constructor(private dashboardService: DashboardService) {}

  ngOnInit() {
    this.dashboardService.summary().subscribe({
      next: (data) => (this.summary = data),
      error: () => (this.error = 'Could not load dashboard.')
    });
    this.loadCompare();
  }

  loadCompare() {
    this.compareError = '';
    this.dashboardService.compare(this.monthsToShow).subscribe({
      next: (data) => {
        this.compareMonths = data.months;
        this.maxValue = Math.max(
          1,
          ...data.months.map((m) => Math.max(m.total_income, m.total_expenses))
        );
      },
      error: () => (this.compareError = 'Could not load month comparison.')
    });
  }

  scaledHeight(value: number): number {
    // Scale bars to a 150px max height based on the largest value in the window.
    return Math.max(2, (value / this.maxValue) * 150);
  }

  get categoryNames(): string[] {
    const names = new Set<string>();
    this.compareMonths.forEach((m) => m.categories.forEach((c) => names.add(c.name)));
    return Array.from(names);
  }

  spentFor(month: MonthEntry, name: string): number {
    const cat = month.categories.find((c) => c.name === name);
    return cat ? cat.spent_this_month : 0;
  }

  statusFor(month: MonthEntry, name: string): string | null {
    const cat = month.categories.find((c) => c.name === name);
    return cat ? cat.status : null;
  }
}
