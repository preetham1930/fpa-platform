import React, { useState, useEffect } from 'react';
import { getErpRuns, triggerErpSync, PERIOD } from './api';
import type { SyncRun, RejectedRecord } from './types';

const IntegrationHub: React.FC = () => {
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [expandedRuns, setExpandedRuns] = useState<Set<number>>(new Set());

  const fetchRuns = async () => {
    try {
      const data = await getErpRuns();
      setRuns(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch integration runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await triggerErpSync(PERIOD);
      await fetchRuns();
    } catch (err: any) {
      alert(err.message || 'Failed to trigger sync');
    } finally {
      setSyncing(false);
    }
  };

  const toggleExpand = (runId: number) => {
    setExpandedRuns(prev => {
      const next = new Set(prev);
      if (next.has(runId)) next.delete(runId);
      else next.add(runId);
      return next;
    });
  };

  if (loading) {
    return <div className="loading">Loading integrations...</div>;
  }

  if (error) {
    return <div className="loading" style={{ color: 'var(--unfavorable)' }}>{error}</div>;
  }

  return (
    <div>
      <div className="header" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '1.5rem' }}>
          <h1>ERP Integration Hub</h1>
          <span className="period-badge">Period: {PERIOD}</span>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: syncing ? 'var(--text-hint)' : 'var(--text)',
            color: 'var(--surface)',
            fontWeight: 600,
            cursor: syncing ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s',
          }}
        >
          {syncing ? 'Syncing...' : 'Sync from SAP'}
        </button>
      </div>

      <div className="panel">
        <h2 className="panel-title">Sync History</h2>
        
        {runs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>No syncs yet — click "Sync from SAP" to fetch actuals.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th className="number-col">Fetched</th>
                  <th className="number-col">Synced</th>
                  <th className="number-col">Rejected</th>
                  <th style={{ textAlign: 'right' }}>Finished At</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => {
                  const isExpanded = expandedRuns.has(run.id);
                  let rejectedRecords: RejectedRecord[] = [];
                  if (run.error_detail) {
                    try {
                      rejectedRecords = JSON.parse(run.error_detail);
                    } catch (e) {
                      console.error("Failed to parse error_detail for run", run.id);
                    }
                  }

                  const hasRejections = rejectedRecords.length > 0;

                  let badgeClass = 'status-badge neutral';
                  if (run.status === 'success') badgeClass = 'status-badge favorable-badge';
                  else if (run.status === 'partial') badgeClass = 'status-badge accent-badge';
                  else if (run.status === 'failed') badgeClass = 'status-badge unfavorable-badge';

                  return (
                    <React.Fragment key={run.id}>
                      <tr style={{ backgroundColor: hasRejections && isExpanded ? 'var(--bg)' : 'transparent' }}>
                        <td style={{ fontWeight: 500 }}>#{run.id}</td>
                        <td>
                          <span className={badgeClass}>{run.status}</span>
                        </td>
                        <td className="number-col">{run.records_fetched}</td>
                        <td className="number-col favorable">{run.records_synced}</td>
                        <td className="number-col">
                          {hasRejections ? (
                            <button
                              onClick={() => toggleExpand(run.id)}
                              style={{
                                background: 'transparent',
                                border: '1px solid var(--border)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                color: 'var(--unfavorable)',
                                fontWeight: 600,
                                fontSize: '0.85rem'
                              }}
                            >
                              {run.records_rejected} rejected — {isExpanded ? 'Hide details' : 'View details'}
                            </button>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>0</span>
                          )}
                        </td>
                        <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                          {run.finished_at ? new Date(run.finished_at).toLocaleString() : '—'}
                        </td>
                      </tr>
                      {isExpanded && hasRejections && (
                        <tr style={{ backgroundColor: 'var(--bg)' }}>
                          <td colSpan={6} style={{ padding: '0' }}>
                            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', borderTop: '1px solid var(--border)' }}>
                              <h4 style={{ marginBottom: '1rem', color: 'var(--unfavorable)' }}>Validation Failures ({rejectedRecords.length})</h4>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {rejectedRecords.map((rej, idx) => (
                                  <div key={idx} style={{ 
                                    background: 'var(--surface)', 
                                    padding: '1rem', 
                                    borderRadius: '8px',
                                    border: '1px solid var(--border)',
                                    borderLeft: '4px solid var(--unfavorable)'
                                  }}>
                                    <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text)' }}>
                                      {rej.reason || rej.error || 'Unknown error'}
                                    </div>
                                    {rej.record && (
                                      <pre style={{ 
                                        margin: 0, 
                                        fontSize: '0.85rem', 
                                        color: 'var(--text-muted)',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-all',
                                        fontFamily: 'monospace'
                                      }}>
                                        {JSON.stringify(rej.record, null, 2)}
                                      </pre>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegrationHub;
