import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface VarianceItem {
  department: string;
  account: string;
  account_type: "revenue" | "cost";
  budget: number;
  actual: number;
  variance: number;
  variance_percentage: number | null;
  is_favorable: boolean;
}

interface VarianceReport {
  period: string;
  items: VarianceItem[];
}

function App() {
  const [data, setData] = useState<VarianceReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get<VarianceReport>('http://localhost:8000/variance?period=1');
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

  // Group data by department for the chart
  const chartData = useMemo(() => {
    if (!data) return [];
    
    const grouped = data.items.reduce((acc, item) => {
      if (!acc[item.department]) {
        acc[item.department] = { name: item.department, Budget: 0, Actual: 0 };
      }
      acc[item.department].Budget += item.budget;
      acc[item.department].Actual += item.actual;
      return acc;
    }, {} as Record<string, { name: string, Budget: number, Actual: number }>);
    
    return Object.values(grouped);
  }, [data]);

  if (loading) {
    return <div className="loading">Loading FP&A Data...</div>;
  }

  if (!data) {
    return <div className="loading">Failed to load data. Ensure backend is running.</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="header">
        <h1>FP&A Variance Dashboard</h1>
        <span className="period-badge">Period: {data.period}</span>
      </div>

      <div className="panel">
        <h2 className="panel-title">Department Overview (Budget vs Actual)</h2>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3643" vertical={false} />
              <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} tickFormatter={(val) => `$${val / 1000}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#181b21', borderColor: '#2e3643', color: '#e2e8f0', borderRadius: '8px' }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar dataKey="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Actual" fill="#10b981" radius={[4, 4, 0, 0]} />
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
                    <td><span className="period-badge">{item.account_type}</span></td>
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
    </div>
  );
}

export default App;
