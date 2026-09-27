import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

export interface DashboardSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  categories: {
    id: number;
    name: string;
    effective_budget: number;
    spent_this_month: number;
    remaining_balance: number;
    status: string | null;
  }[];
}

export interface MonthEntry {
  month: string;
  total_income: number;
  total_expenses: number;
  categories: {
    id: number;
    name: string;
    spent_this_month: number;
    status: string | null;
  }[];
}

export interface CompareResponse {
  months: MonthEntry[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  constructor(private http: HttpClient) {}

  summary() {
    return this.http.get<DashboardSummary>(`${API_BASE}/dashboard/summary`, { withCredentials: true });
  }

  compare(months: number = 6) {
    return this.http.get<CompareResponse>(`${API_BASE}/dashboard/compare?months=${months}`, { withCredentials: true });
  }
}
