import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_BASE } from './api-base';

export interface Transaction {
  id: number;
  type: 'income' | 'expense';
  amount: number;
  category_id: number | null;
  spent_on: string;
  note: string | null;
}

export interface TransactionResponse extends Transaction {
  budget_warning: string | null;
  overall_warning: string | null;
}

@Injectable({ providedIn: 'root' })
export class TransactionsService {
  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<Transaction[]>(`${API_BASE}/transactions`, { withCredentials: true });
  }

  create(payload: { type: string; amount: number; category_id?: number | null; spent_on: string; note?: string }) {
    return this.http.post<TransactionResponse>(`${API_BASE}/transactions`, payload, { withCredentials: true });
  }
}
