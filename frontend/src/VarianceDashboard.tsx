import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import type { VarianceReport } from './types';
import { API_BASE_URL, PERIOD } from './api';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <div className="tooltip-title">{label}</div>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="tooltip-item">
            <span className="label" style={{ color: entry.color }}>{entry.name}:</span>
            <span className="value numeric">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(entry.value as number)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const CustomXAxisTick = ({ x, y, payload }: any) => {
  if (!payload || !payload.value) return null;
  const parts = payload.value.split(' - ');
  const dept = parts[0];
  const acc = parts.slice(1).join(' - ');
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={40} textAnchor="middle" fill="var(--text-muted)" fontSize={12}>
        <tspan x={0} dy="0">{dept}</tspan>
        {acc && <tspan x={0} dy="16">{acc}</tspan>}
      </text>
    </g>
  );
};

export default function VarianceDashboard() {
  const [data, setData] = useState<VarianceReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get<VarianceReport>(`${API_BASE_URL}/variance?period=${PERIOD}`);
        setData(response.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number | null) => {
    if (value === null) return 'N/A';
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const { revKpi, costKpi, itemStats } = useMemo(() => {
    if (!data) return { revKpi: null, costKpi: null, itemStats: null };
    
    let revActual = 0;
    let revBudget = 0;
    let costActual = 0;
    let costBudget = 0;
    let favorableCount = 0;
    let unfavorableCount = 0;

    data.items.forEach(item => {
      if (item.account_type === 'revenue') {
        revActual += item.actual;
        revBudget += item.budget;
      } else {
        costActual += item.actual;
        costBudget += item.budget;
      }

      if (item.is_favorable) {
        favorableCount++;
      } else {
        unfavorableCount++;
      }
    });

    const revVariance = revActual - revBudget;
    const revPct = revBudget !== 0 ? (revVariance / Math.abs(revBudget)) * 100 : null;
    const revFavorable = revVariance >= 0;

    const costVariance = costActual - costBudget;
    const costPct = costBudget !== 0 ? (costVariance / Math.abs(costBudget)) * 100 : null;
    const costFavorable = costVariance <= 0;

    return {
      revKpi: { actual: revActual, budget: revBudget, pct: revPct, isFavorable: revFavorable },
      costKpi: { actual: costActual, budget: costBudget, pct: costPct, isFavorable: costFavorable },
      itemStats: { total: data.items.length, favorable: favorableCount, unfavorable: unfavorableCount }
    };
  }, [data]);

  const chartData = useMemo(() => {
    if (!data) return [];
    
    const grouped = data.items.reduce((acc, item) => {
      const key = `${item.department} - ${item.account}`;
      if (!acc[key]) {
        acc[key] = { name: key, Budget: 0, Actual: 0 };
      }
      acc[key].Budget += item.budget;
      acc[key].Actual += item.actual;
      return acc;
    }, {} as Record<string, { name: string, Budget: number, Actual: number }>);
    
    return Object.values(grouped);
  }, [data]);

  if (loading) {
    return <div className="loading">Loading FP&A Data...</div>;
  }

  if (!data || !revKpi || !costKpi || !itemStats) {
    return <div className="loading">Failed to load data. Ensure backend is running.</div>;
  }

  return (
    <>
      <div className="header">
        <h1>FP&A Variance Dashboard</h1>
        <span className="period-badge numeric">Period: {data.period}</span>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Revenue</div>
          <div className="kpi-value numeric">{formatCurrency(revKpi.actual)}</div>
          <div className="kpi-subtext">
            <span className="numeric">{formatCurrency(revKpi.budget)} budget</span>
            <span>&middot;</span>
            <span className={`numeric ${revKpi.isFavorable ? 'favorable' : 'unfavorable'}`}>
              {formatPercent(revKpi.pct)} {revKpi.isFavorable ? 'favorable' : 'unfavorable'}
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Total Cost</div>
          <div className="kpi-value numeric">{formatCurrency(costKpi.actual)}</div>
          <div className="kpi-subtext">
            <span className="numeric">{formatCurrency(costKpi.budget)} budget</span>
            <span>&middot;</span>
            <span className={`numeric ${costKpi.isFavorable ? 'favorable' : 'unfavorable'}`}>
              {formatPercent(costKpi.pct)} {costKpi.isFavorable ? 'favorable' : 'unfavorable'}
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Line Items</div>
          <div className="kpi-value numeric">{itemStats.total}</div>
          <div className="kpi-subtext">
            <span className="numeric favorable">{itemStats.favorable} Favorable</span>
            <span>&middot;</span>
            <span className="numeric unfavorable">{itemStats.unfavorable} Unfavorable</span>
          </div>
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Department Overview</h2>
        <div className="chart-container" style={{ height: '420px', paddingBottom: '10px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
              barGap={4}
            >
              <XAxis 
                dataKey="name" 
                stroke="var(--text-hint)" 
                tick={<CustomXAxisTick />}
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
                interval={0}
                tickMargin={20}
              />
              <YAxis 
                stroke="var(--text-hint)" 
                tick={{ fill: 'var(--text-muted)' }} 
                axisLine={false}
                tickLine={false}
                tickFormatter={(val) => `$${val / 1000}k`} 
                className="numeric"
              />
              <Tooltip 
                cursor={{ fill: 'transparent' }} 
                content={<CustomTooltip />}
              />
              <Legend 
                verticalAlign="top"
                wrapperStyle={{ paddingBottom: '20px', color: 'var(--text-muted)' }} 
                iconType="circle"
              />
              <Bar dataKey="Budget" fill="var(--bar-budget)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Actual" fill="var(--bar-actual)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Detailed Variance Report</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Account</th>
                <th>Type</th>
                <th className="number-col">Budget</th>
                <th className="number-col">Actual</th>
                <th className="number-col">Variance</th>
                <th className="number-col">Var %</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item, idx) => {
                const isUnfavorable = !item.is_favorable && item.variance !== 0;
                
                return (
                  <tr key={idx} className={isUnfavorable ? 'unfavorable-row' : ''}>
                    <td>{item.department}</td>
                    <td>{item.account}</td>
                    <td style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      {item.account_type}
                    </td>
                    <td className="number-col">{formatCurrency(item.budget)}</td>
                    <td className="number-col">{formatCurrency(item.actual)}</td>
                    <td className={`number-col ${isUnfavorable ? 'unfavorable' : 'favorable'}`}>
                      {formatCurrency(item.variance)}
                    </td>
                    <td className={`number-col ${isUnfavorable ? 'unfavorable' : 'favorable'}`}>
                      {formatPercent(item.variance_percentage)}
                    </td>
                    <td>
                      <span className={`status-badge ${isUnfavorable ? 'unfavorable-badge' : 'favorable-badge'}`}>
                        {item.is_favorable ? 'Favorable' : 'Unfavorable'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
