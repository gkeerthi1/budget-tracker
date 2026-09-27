import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoalsService, SavingsGoal } from '../../services/goals.service';

@Component({
  selector: 'app-goals',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h2>Savings Goals</h2>

    <form (ngSubmit)="addGoal()" class="form-grid">
      <label>
        Name
        <input type="text" [(ngModel)]="name" name="name" required data-testid="goal-name-input" />
      </label>
      <label>
        Target amount
        <input type="number" [(ngModel)]="targetAmount" name="targetAmount" required data-testid="goal-amount-input" />
      </label>
      <label>
        Target date
        <input type="date" [(ngModel)]="targetDate" name="targetDate" required data-testid="goal-date-input" />
      </label>
      <button type="submit" data-testid="add-goal-btn">Add goal</button>
    </form>
    <p class="hint">Target date must be in the future.</p>

    <p *ngIf="error" class="error" data-testid="goal-error">{{ error }}</p>

    <div *ngFor="let g of goals" class="goal-card" [attr.data-testid]="'goal-card-' + g.id">
      <div class="goal-header">
        <strong>{{ g.name }}</strong>
        <button (click)="deleteGoal(g.id)" data-testid="delete-goal-btn">Delete</button>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" [style.width.%]="g.percent_complete"></div>
      </div>

      <div class="goal-stats">
        <span>{{ g.current_amount }} / {{ g.target_amount }} ({{ g.percent_complete }}%)</span>
        <span>Target: {{ g.target_date }}</span>
        <span>{{ g.months_left }} months left</span>
        <span>Need {{ g.required_monthly_contribution }}/month</span>
      </div>

      <form (ngSubmit)="addContribution(g)" class="contribute-form">
        <input type="number" [(ngModel)]="contributionAmounts[g.id]" name="contribute-{{ g.id }}"
               placeholder="Amount" [attr.data-testid]="'contribute-input-' + g.id" />
        <button type="submit" [attr.data-testid]="'contribute-btn-' + g.id">Add contribution</button>
      </form>
    </div>

    <p *ngIf="!goals.length">No savings goals yet.</p>
  `,
  styles: [`
    .form-grid { display: flex; gap: 10px; flex-wrap: wrap; align-items: end; margin-bottom: 4px; }
    label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
    input { padding: 6px; }
    .hint { color: #555; font-size: 12px; margin-bottom: 16px; }
    .error { color: #b00020; }

    .goal-card {
      border: 1px solid #ddd;
      border-radius: 6px;
      padding: 14px;
      margin-bottom: 14px;
    }
    .goal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .progress-bar { background: #eee; border-radius: 4px; height: 10px; overflow: hidden; margin-bottom: 8px; }
    .progress-fill { background: #2e7d32; height: 100%; }
    .goal-stats { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: #444; margin-bottom: 10px; }
    .contribute-form { display: flex; gap: 8px; }
    .contribute-form input { width: 120px; }
  `]
})
export class GoalsComponent implements OnInit {
  goals: SavingsGoal[] = [];
  name = '';
  targetAmount: number | null = null;
  targetDate = '';
  error = '';
  contributionAmounts: { [id: number]: number } = {};

  constructor(private goalsService: GoalsService) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.goalsService.list().subscribe({
      next: (data) => (this.goals = data),
      error: () => (this.error = 'Could not load goals.')
    });
  }

  addGoal() {
    this.error = '';
    if (this.targetAmount === null) return;
    this.goalsService.create(this.name, this.targetAmount, this.targetDate).subscribe({
      next: () => {
        this.name = '';
        this.targetAmount = null;
        this.targetDate = '';
        this.load();
      },
      error: (err) => (this.error = err?.error?.error || 'Could not add goal.')
    });
  }

  addContribution(goal: SavingsGoal) {
    const amount = this.contributionAmounts[goal.id];
    if (!amount) return;
    this.goalsService.contribute(goal.id, amount).subscribe({
      next: () => {
        this.contributionAmounts[goal.id] = 0;
        this.load();
      },
      error: (err) => (this.error = err?.error?.error || 'Could not add contribution.')
    });
  }

  deleteGoal(id: number) {
    this.goalsService.delete(id).subscribe({
      next: () => this.load(),
      error: () => (this.error = 'Could not delete goal.')
    });
  }
}
