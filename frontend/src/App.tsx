import { useState } from 'react';
import VarianceDashboard from './VarianceDashboard';
import ScenarioPlanning from './ScenarioPlanning';
import ComparisonView from './ComparisonView';
import IntegrationHub from './IntegrationHub';

function App() {
  const [view, setView] = useState<'variance' | 'scenario' | 'comparison' | 'integrations'>('variance');

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
        <button 
          onClick={() => setView('comparison')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: view === 'comparison' ? 'var(--text)' : 'transparent',
            color: view === 'comparison' ? 'var(--surface)' : 'var(--text-muted)',
            transition: 'all 0.2s ease'
          }}
        >
          Comparison
        </button>
        <button 
          onClick={() => setView('integrations')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: view === 'integrations' ? 'var(--text)' : 'transparent',
            color: view === 'integrations' ? 'var(--surface)' : 'var(--text-muted)',
            transition: 'all 0.2s ease'
          }}
        >
          Integrations
        </button>
      </div>

      {view === 'variance' && <VarianceDashboard />}
      {view === 'scenario' && <ScenarioPlanning />}
      {view === 'comparison' && <ComparisonView />}
      {view === 'integrations' && <IntegrationHub />}
    </div>
  );
}

export default App;
