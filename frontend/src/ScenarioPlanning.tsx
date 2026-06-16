import { useEffect, useState, useMemo, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL, PERIOD } from './api';
import type { Scenario, DriverValue, ForecastReport } from './types';

export default function ScenarioPlanning() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(null);
  const [drivers, setDrivers] = useState<DriverValue[]>([]);
  const [forecast, setForecast] = useState<ForecastReport | null>(null);

  const [loadingScenarios, setLoadingScenarios] = useState(true);
  const [loadingDrivers, setLoadingDrivers] = useState(false);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const activeScenario = scenarios.find(s => s.id === activeScenarioId);
  const isBaseline = activeScenario?.is_baseline ?? true;

  // Track the latest forecast fetch to ignore out-of-order responses
  const fetchIdRef = useRef(0);
  const debounceTimerRef = useRef<number | null>(null);

  // 1. Load Scenarios
  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const res = await axios.get<Scenario[]>(`${API_BASE_URL}/scenarios`);
        setScenarios(res.data);
        const base = res.data.find(s => s.is_baseline);
        if (base) {
          setActiveScenarioId(base.id);
        } else if (res.data.length > 0) {
          setActiveScenarioId(res.data[0].id);
        }
      } catch (err) {
        console.error("Error fetching scenarios", err);
      } finally {
        setLoadingScenarios(false);
      }
    };
    fetchScenarios();
  }, []);

  // 2. Load Drivers & Forecast when active scenario changes
  useEffect(() => {
    if (activeScenarioId === null) return;

    const fetchScenarioData = async () => {
      setLoadingDrivers(true);
      setLoadingForecast(true);
      try {
        const drvRes = await axios.get<DriverValue[]>(`${API_BASE_URL}/scenarios/${activeScenarioId}/drivers`);
        setDrivers(drvRes.data);

        fetchForecast(activeScenarioId);
      } catch (err) {
        console.error("Error fetching scenario data", err);
        setLoadingDrivers(false);
        setLoadingForecast(false);
      }
    };
    fetchScenarioData();
  }, [activeScenarioId]);

  const fetchForecast = async (scenarioId: number) => {
    const currentFetchId = ++fetchIdRef.current;
    setIsUpdating(true);
    try {
      const res = await axios.get<ForecastReport>(`${API_BASE_URL}/forecast?scenario=${scenarioId}&period=${PERIOD}`);
      if (currentFetchId === fetchIdRef.current) {
        setForecast(res.data);
      }
    } catch (err) {
      console.error("Error fetching forecast", err);
    } finally {
      if (currentFetchId === fetchIdRef.current) {
        setIsUpdating(false);
        setLoadingDrivers(false);
        setLoadingForecast(false);
      }
    }
  };

  // 3. Handle Driver Edit
  const handleDriverChange = (driverId: number, newValueStr: string) => {
    const newValue = parseFloat(newValueStr) || 0;

    // Optimistically update local state
    setDrivers(prev => prev.map(d => 
      d.driver_id === driverId ? { ...d, value: newValue } : d
    ));

    // Debounce the API call
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = window.setTimeout(async () => {
      if (activeScenarioId === null) return;
      try {
        setIsUpdating(true);
        await axios.put(`${API_BASE_URL}/scenarios/${activeScenarioId}/drivers/${driverId}`, {
          value: newValue
        });
        // Refetch forecast to get updated math
        await fetchForecast(activeScenarioId);
      } catch (err) {
        console.error("Error updating driver", err);
        setIsUpdating(false);
      }
    }, 400);
  };

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
    if (!forecast) return { revKpi: null, costKpi: null, itemStats: null };
    
    let revForecast = 0;
    let revBudget = 0;
    let costForecast = 0;
    let costBudget = 0;
    let favorableCount = 0;
    let unfavorableCount = 0;

    forecast.items.forEach(item => {
      if (item.account_type === 'revenue') {
        revForecast += item.forecast;
        revBudget += item.budget;
      } else {
        costForecast += item.forecast;
        costBudget += item.budget;
      }

      if (item.is_favorable) {
        favorableCount++;
      } else {
        unfavorableCount++;
      }
    });

    const revVariance = revForecast - revBudget;
    const revPct = revBudget !== 0 ? (revVariance / Math.abs(revBudget)) * 100 : null;
    const revFavorable = revVariance >= 0;

    const costVariance = costForecast - costBudget;
    const costPct = costBudget !== 0 ? (costVariance / Math.abs(costBudget)) * 100 : null;
    const costFavorable = costVariance <= 0;

    return {
      revKpi: { forecast: revForecast, budget: revBudget, pct: revPct, isFavorable: revFavorable },
      costKpi: { forecast: costForecast, budget: costBudget, pct: costPct, isFavorable: costFavorable },
      itemStats: { total: forecast.items.length, favorable: favorableCount, unfavorable: unfavorableCount }
    };
  }, [forecast]);

  if (loadingScenarios) {
    return <div className="loading">Loading Scenarios...</div>;
  }

  return (
    <>
      <div className="header" style={{ marginBottom: '20px' }}>
        <h1>Scenario Planning</h1>
        <span className="period-badge numeric">Period: {PERIOD}</span>
      </div>

      <div className="panel" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
          <label style={{ fontWeight: 600 }}>Active Scenario:</label>
          <select 
            value={activeScenarioId || ''} 
            onChange={(e) => setActiveScenarioId(parseInt(e.target.value))}
            style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '1rem' }}
          >
            {scenarios.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          {isUpdating && <span style={{ color: 'var(--accent)', fontSize: '0.9rem' }}>Updating forecast...</span>}
        </div>

        {isBaseline && (
          <div style={{ padding: '12px', backgroundColor: 'var(--accent-soft)', borderRadius: '8px', color: 'var(--text)', marginBottom: '16px', fontSize: '0.95rem' }}>
            <strong>Note:</strong> The Baseline scenario is locked. Switch to Upside or Downside to edit drivers and model changes.
          </div>
        )}

        <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem' }}>Drivers</h3>
        {loadingDrivers ? (
          <div className="loading" style={{ height: '50px' }}>Loading drivers...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
            {drivers.map(dv => (
              <div key={dv.id} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {dv.driver.label} ({dv.driver.unit})
                </label>
                <input 
                  type="number" 
                  value={dv.value}
                  disabled={isBaseline}
                  onChange={(e) => handleDriverChange(dv.driver.id, e.target.value)}
                  style={{
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    backgroundColor: isBaseline ? 'var(--bg)' : 'var(--surface)',
                    color: 'var(--text)'
                  }}
                  className="numeric"
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {!loadingForecast && forecast && revKpi && costKpi && itemStats ? (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Total Revenue (Forecast)</div>
              <div className="kpi-value numeric">{formatCurrency(revKpi.forecast)}</div>
              <div className="kpi-subtext">
                <span className="numeric">{formatCurrency(revKpi.budget)} budget</span>
                <span>&middot;</span>
                <span className={`numeric ${revKpi.isFavorable ? 'favorable' : 'unfavorable'}`}>
                  {formatPercent(revKpi.pct)} {revKpi.isFavorable ? 'favorable' : 'unfavorable'}
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Total Cost (Forecast)</div>
              <div className="kpi-value numeric">{formatCurrency(costKpi.forecast)}</div>
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

          <div className="panel" style={{ marginTop: '20px' }}>
            <h2 className="panel-title">Forecast vs Budget Report</h2>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Department</th>
                    <th>Account</th>
                    <th>Type</th>
                    <th className="number-col">Budget</th>
                    <th className="number-col">Forecast</th>
                    <th className="number-col">Variance</th>
                    <th className="number-col">Var %</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.items.map((item, idx) => {
                    const isUnfavorable = !item.is_favorable && item.variance !== 0;
                    
                    return (
                      <tr key={idx} className={isUnfavorable ? 'unfavorable-row' : ''}>
                        <td>{item.department}</td>
                        <td>{item.account}</td>
                        <td style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                          {item.account_type}
                        </td>
                        <td className="number-col">{formatCurrency(item.budget)}</td>
                        <td className="number-col">{formatCurrency(item.forecast)}</td>
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
      ) : (
        <div className="loading">Loading Forecast...</div>
      )}
    </>
  );
}
