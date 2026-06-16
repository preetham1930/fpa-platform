import { useState } from 'react';
import VarianceDashboard from './VarianceDashboard';
import ScenarioPlanning from './ScenarioPlanning';

function App() {
  const [view, setView] = useState<'variance' | 'scenario'>('variance');

  return (
    <div className="dashboard-container">
      {/* Top Level Navigation */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
        <button 
          onClick={() => setView('variance')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: view === 'variance' ? 'var(--text)' : 'transparent',
            color: view === 'variance' ? 'var(--surface)' : 'var(--text-muted)',
            transition: 'all 0.2s ease'
          }}
        >
          Variance
        </button>
        <button 
          onClick={() => setView('scenario')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: view === 'scenario' ? 'var(--text)' : 'transparent',
            color: view === 'scenario' ? 'var(--surface)' : 'var(--text-muted)',
            transition: 'all 0.2s ease'
          }}
        >
          Scenario Planning
        </button>
      </div>

      {view === 'variance' ? <VarianceDashboard /> : <ScenarioPlanning />}
    </div>
  );
}

export default App;
