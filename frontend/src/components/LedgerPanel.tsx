'use client';

import React, { useEffect, useRef } from 'react';
import { formatTime, formatCategory, AuditLogEntry } from '../lib/api';

interface LedgerPanelProps {
  logs: AuditLogEntry[];
}

export default function LedgerPanel({ logs }: LedgerPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="8" y1="6" x2="21" y2="6"></line>
            <line x1="8" y1="12" x2="21" y2="12"></line>
            <line x1="8" y1="18" x2="21" y2="18"></line>
            <line x1="3" y1="6" x2="3.01" y2="6"></line>
            <line x1="3" y1="12" x2="3.01" y2="12"></line>
            <line x1="3" y1="18" x2="3.01" y2="18"></line>
          </svg>
          Audit Ledger
        </div>
        <div className="eyebrow">Immutable</div>
      </div>
      
      <div className="ledger-area" ref={containerRef}>
        {logs.length === 0 ? (
          <div className="empty-state">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.5 }}>
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span style={{ fontSize: 'var(--text-sm)' }}>Waiting for activity...</span>
          </div>
        ) : (
          <table className="ledger-table">
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="ledger-row animate-flash">
                  <td className="ledger-cell time">{formatTime(log.timestamp)}</td>
                  <td className="ledger-cell category">
                    {log.flags.length > 0 
                      ? formatCategory(log.flags[0].category)
                      : 'None'}
                  </td>
                  <td className="ledger-cell action">
                    {log.action === 'approved' && (
                       <>Approved <span className="status-dot" style={{ background: 'var(--accent-teal)' }} /></>
                    )}
                    {log.action === 'rejected' && (
                       <>Rejected <span className="status-dot" style={{ background: 'var(--accent-red)' }} /></>
                    )}
                    {log.action === 'sent' && (
                       <>Sent <span className="status-dot" style={{ background: 'var(--accent-teal)' }} /></>
                    )}
                    {log.action === 'held' && (
                       <>HELD <span className="status-dot" style={{ background: 'var(--accent-amber)' }} /></>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
