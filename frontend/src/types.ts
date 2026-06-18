export interface VarianceItem {
  department: string;
  account: string;
  account_type: "revenue" | "cost";
  budget: number;
  actual: number;
  variance: number;
  variance_percentage: number | null;
  is_favorable: boolean;
}

export interface VarianceReport {
  period: string;
  items: VarianceItem[];
}

export interface Scenario {
  id: number;
  name: string;
  description: string | null;
  is_baseline: boolean;
}

export interface Driver {
  id: number;
  key: string;
  label: string;
  unit: string;
}

export interface DriverValue {
  id: number;
  driver_id: number;
  scenario_id: number;
  value: number;
  driver: Driver;
}

export interface ForecastItem {
  department: string;
  account: string;
  account_type: "revenue" | "cost";
  budget: number;
  forecast: number;
  variance: number;
  variance_percentage: number | null;
  is_favorable: boolean;
}

export interface ForecastReport {
  scenario_id: number;
  period: string;
  items: ForecastItem[];
}

export interface CompareScenarioResult {
  forecast: number;
  variance: number;
  variance_percentage: number | null;
  is_favorable: boolean;
}

export interface CompareItem {
  department: string;
  account: string;
  account_type: "revenue" | "cost";
  budget: number;
  scenarios: Record<number, CompareScenarioResult>;
}

export interface CompareReport {
  period: string;
  items: CompareItem[];
}

export interface RejectedRecord {
  record?: Record<string, any>;
  reason?: string;
  error?: string;
}

export interface SyncRun {
  id: number;
  source: string;
  period: string;
  status: 'success' | 'partial' | 'failed';
  records_fetched: number;
  records_synced: number;
  records_rejected: number;
  started_at: string | null;
  finished_at: string | null;
  error_detail: string | null;
}

export interface TransactionAggregate {
  department: string;
  account: string;
  total_amount: number;
  event_count: number;
}

export interface TransactionInsightsReport {
  total_events: number;
  total_amount: number;
  aggregates: TransactionAggregate[];
}

