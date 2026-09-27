import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

export interface Category {
  id: number;
  name: string;
  monthly_budget: number;
  rollover_amount: number;
  effective_budget: number;
  spent_this_month: number;
  remaining_balance: number;
  status: string | null;
}

@Injectable({ providedIn: 'root' })
export class CategoriesService {
  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<Category[]>(`${API_BASE}/categories`, { withCredentials: true });
  }

  create(name: string, monthly_budget: number) {
    return this.http.post<Category>(`${API_BASE}/categories`, { name, monthly_budget }, { withCredentials: true });
  }

  update(id: number, monthly_budget: number) {
    return this.http.put<Category>(`${API_BASE}/categories/${id}`, { monthly_budget }, { withCredentials: true });
  }

  delete(id: number) {
    return this.http.delete(`${API_BASE}/categories/${id}`, { withCredentials: true });
  }
}
