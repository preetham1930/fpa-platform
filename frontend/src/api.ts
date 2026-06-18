export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const PERIOD = '2026-05';

import type { SyncRun } from './types';

export const triggerErpSync = async (period: string): Promise<SyncRun> => {
  const response = await fetch(`${API_BASE_URL}/integrations/erp/sync?period=${period}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to trigger ERP sync');
  }
  return response.json();
};

export const getErpRuns = async (): Promise<SyncRun[]> => {
  const response = await fetch(`${API_BASE_URL}/integrations/erp/runs`);
  if (!response.ok) {
    throw new Error('Failed to fetch ERP runs');
  }
  return response.json();
};

import type { TransactionInsightsReport } from './types';

export const getTransactionInsights = async (): Promise<TransactionInsightsReport> => {
  const response = await fetch(`${API_BASE_URL}/analytics/transactions`);
  if (!response.ok) {
    throw new Error('Failed to fetch transaction insights');
  }
  return response.json();
};
