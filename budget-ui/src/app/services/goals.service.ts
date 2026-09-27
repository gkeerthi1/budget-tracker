import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

export interface SavingsGoal {
  id: number;
  name: string;
  target_amount: number;
  target_date: string;
  current_amount: number;
  remaining_amount: number;
  months_left: number;
  required_monthly_contribution: number;
  percent_complete: number;
}

@Injectable({ providedIn: 'root' })
export class GoalsService {
  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<SavingsGoal[]>(`${API_BASE}/goals`, { withCredentials: true });
  }

  create(name: string, target_amount: number, target_date: string) {
    return this.http.post<SavingsGoal>(`${API_BASE}/goals`, { name, target_amount, target_date }, { withCredentials: true });
  }

  contribute(id: number, amount: number) {
    return this.http.post<SavingsGoal>(`${API_BASE}/goals/${id}/contribute`, { amount }, { withCredentials: true });
  }

  delete(id: number) {
    return this.http.delete(`${API_BASE}/goals/${id}`, { withCredentials: true });
  }
}
