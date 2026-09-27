import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

export interface RecurringRule {
  id: number;
  type: 'income' | 'expense';
  amount: number;
  category_id: number | null;
  day_of_month: number;
  note: string | null;
}

@Injectable({ providedIn: 'root' })
export class RecurringService {
  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<RecurringRule[]>(`${API_BASE}/recurring`, { withCredentials: true });
  }

  create(payload: { type: string; amount: number; day_of_month: number; category_id?: number | null; note?: string }) {
    return this.http.post<RecurringRule>(`${API_BASE}/recurring`, payload, { withCredentials: true });
  }

  delete(id: number) {
    return this.http.delete(`${API_BASE}/recurring/${id}`, { withCredentials: true });
  }
}
