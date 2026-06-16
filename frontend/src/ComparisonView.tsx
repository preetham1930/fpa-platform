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
import type { Scenario, CompareReport } from './types';
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

export default function ComparisonView() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [compareData, setCompareData] = useState<CompareReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const scenariosRes = await axios.get<Scenario[]>(`${API_BASE_URL}/scenarios`);
        
        // Sort scenarios: Baseline first, then by ID
        const sortedScenarios = scenariosRes.data.sort((a, b) => {
          if (a.is_baseline && !b.is_baseline) return -1;
          if (!a.is_baseline && b.is_baseline) return 1;
          return a.id - b.id;
        });
        setScenarios(sortedScenarios);

        const scenarioIds = sortedScenarios.map(s => s.id).join(',');
        const compareRes = await axios.get<CompareReport>(`${API_BASE_URL}/forecast/compare?scenarios=${scenarioIds}&period=${PERIOD}`);
        setCompareData(compareRes.data);
      } catch (err) {
        console.error("Error fetching comparison data", err);
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

  const chartData = useMemo(() => {
    if (!compareData || scenarios.length === 0) return [];
    
    return scenarios.map(scenario => {
      let totalRevenue = 0;
      let totalCost = 0;
      
      compareData.items.forEach(item => {
        const scResult = item.scenarios[scenario.id];
        if (scResult) {
          if (item.account_type === 'revenue') {
            totalRevenue += scResult.forecast;
          } else {
            totalCost += scResult.forecast;
          }
        }
      });
      
      return {
        name: scenario.name,
        Revenue: totalRevenue,
        Cost: totalCost
      };
    });
  }, [compareData, scenarios]);

  if (loading) {
    return <div className="loading">Loading Comparison Data...</div>;
  }

  if (!compareData || scenarios.length === 0) {
    return <div className="loading">Failed to load comparison data.</div>;
  }

  return (
    <>
      <div className="header" style={{ marginBottom: '20px' }}>
        <h1>Forecast Comparison</h1>
        <span className="period-badge numeric">Period: {PERIOD}</span>
      </div>

      <div className="panel" style={{ marginBottom: '20px' }}>
        <h2 className="panel-title">Total Revenue vs Total Cost by Scenario</h2>
        <div className="chart-container" style={{ height: '360px', paddingBottom: '30px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              barGap={4}
            >
              <XAxis 
                dataKey="name" 
                stroke="var(--text-hint)" 
                tick={{ fill: 'var(--text-muted)' }} 
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
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
                wrapperStyle={{ paddingTop: '20px', color: 'var(--text-muted)' }} 
                iconType="circle"
              />
              <Bar dataKey="Revenue" fill="var(--bar-budget)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Cost" fill="var(--bar-actual)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Detailed Comparison</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Account</th>
                <th>Type</th>
                <th className="number-col">Budget</th>
                {scenarios.map(s => (
                  <th key={s.id} className="number-col">{s.name} Forecast</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {compareData.items.map((item, idx) => (
                <tr key={idx}>
                  <td>{item.department}</td>
                  <td>{item.account}</td>
                  <td style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                    {item.account_type}
                  </td>
                  <td className="number-col">{formatCurrency(item.budget)}</td>
                  {scenarios.map(s => {
                    const scResult = item.scenarios[s.id];
                    if (!scResult) return <td key={s.id} className="number-col">-</td>;
                    
                    const isUnfavorable = !scResult.is_favorable && scResult.variance !== 0;
                    
                    return (
                      <td key={s.id} className={`number-col ${isUnfavorable ? 'unfavorable' : 'favorable'}`}>
                        {formatCurrency(scResult.forecast)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
