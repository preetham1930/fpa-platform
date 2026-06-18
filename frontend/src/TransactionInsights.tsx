import React, { useState, useEffect, useMemo } from 'react';
import { getTransactionInsights } from './api';
import type { TransactionInsightsReport } from './types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const TransactionInsights: React.FC = () => {
  const [report, setReport] = useState<TransactionInsightsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const data = await getTransactionInsights();
        setReport(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch transaction insights');
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const chartData = useMemo(() => {
    if (!report) return [];
    return report.aggregates.map(agg => ({
      name: `${agg.department} - ${agg.account}`,
      amount: agg.total_amount,
    }));
  }, [report]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <div className="tooltip-title">{label}</div>
          <div className="tooltip-item">
            <span className="label">Total Amount</span>
            <span className="value">{formatCurrency(payload[0].value)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomTick = ({ x, y, payload }: any) => {
    // Split "Department - Account" into two lines
    const parts = payload.value.split(' - ');
    return (
      <g transform={`translate(${x},${y})`}>
        <text x={0} y={0} dy={24} textAnchor="middle" fill="var(--text-muted)" fontSize="0.8rem" fontWeight={500}>
          {parts[0]}
        </text>
        <text x={0} y={0} dy={40} textAnchor="middle" fill="var(--text-muted)" fontSize="0.8rem">
          {parts[1]}
        </text>
      </g>
    );
  };

  if (loading) {
    return <div className="loading">Loading insights...</div>;
  }

  if (error) {
    return <div className="loading" style={{ color: 'var(--unfavorable)' }}>{error}</div>;
  }

  if (!report || report.total_events === 0) {
    return (
      <div>
        <div className="header" style={{ marginBottom: '20px' }}>
          <h1>Transaction Insights</h1>
        </div>
        <div className="panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>No pipeline data yet.</p>
          <p style={{ color: 'var(--text-hint)' }}>The streaming pipeline has not processed any events or the BigQuery table is empty.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="header" style={{ marginBottom: '20px' }}>
        <h1>Transaction Insights</h1>
      </div>

      <div style={{ padding: '16px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', marginBottom: '24px', fontSize: '0.95rem' }}>
        <strong>Powered by the streaming pipeline.</strong> Transaction events flow through Cloud Pub/Sub, are aggregated in 60-second windows by Apache Beam on Dataflow, and land in BigQuery — which this dashboard reads. Figures reflect the latest pipeline run.
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Events Processed</div>
          <div className="kpi-value numeric">{new Intl.NumberFormat('en-US').format(report.total_events)}</div>
          <div className="kpi-subtext">Events ingested via Pub/Sub</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Total Transaction Amount</div>
          <div className="kpi-value numeric">{formatCurrency(report.total_amount)}</div>
          <div className="kpi-subtext">Aggregated via Dataflow windowing</div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: '24px' }}>
        <h2 className="panel-title">Total Amount by Category</h2>
        <div className="chart-container" style={{ height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis 
                dataKey="name" 
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
                interval={0}
                tick={<CustomTick />}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tickFormatter={(val) => `$${val / 1000}k`}
                tick={{ fill: 'var(--text-muted)', fontSize: '0.85rem' }}
                width={80}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg)' }} />
              <Bar dataKey="amount" fill="var(--accent)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Aggregated Results</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Account</th>
                <th className="number-col">Total Amount</th>
                <th className="number-col">Event Count</th>
              </tr>
            </thead>
            <tbody>
              {report.aggregates.map((agg, idx) => (
                <tr key={idx}>
                  <td>{agg.department}</td>
                  <td>{agg.account}</td>
                  <td className="number-col">{formatCurrency(agg.total_amount)}</td>
                  <td className="number-col" style={{ color: 'var(--text-muted)' }}>{new Intl.NumberFormat('en-US').format(agg.event_count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TransactionInsights;
