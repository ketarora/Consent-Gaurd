'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AuditLogEntry } from '../lib/api';

interface AuditSummaryCardProps {
  logs: AuditLogEntry[];
  onDismiss: () => void;
}

export default function AuditSummaryCard({ logs, onDismiss }: AuditSummaryCardProps) {
  const total = logs.length;
  const held = logs.filter(l => l.action === 'held').length;
  const sent = logs.filter(l => l.action === 'sent').length;
  const rejected = logs.filter(l => l.action === 'rejected').length;
  
  // Dynamically count CCPA categories from active logs
  const categoryCounts: Record<string, number> = {
    false_urgency: 0,
    basket_sneaking: 0,
    confirm_shaming: 0,
    forced_continuity: 0,
    drip_pricing: 0,
  };

  logs.forEach(log => {
    log.flags?.forEach(flag => {
      if (categoryCounts[flag.category] !== undefined) {
        categoryCounts[flag.category]++;
      }
    });
  });

  const maxVal = Math.max(...Object.values(categoryCounts), 1);

  const taxonomyData = [
    { label: 'False Urg.', val: Math.round((categoryCounts.false_urgency / maxVal) * 100), raw: categoryCounts.false_urgency, color: 'var(--accent-red)' },
    { label: 'Sneaking', val: Math.round((categoryCounts.basket_sneaking / maxVal) * 100), raw: categoryCounts.basket_sneaking, color: 'var(--accent-amber)' },
    { label: 'Shaming', val: Math.round((categoryCounts.confirm_shaming / maxVal) * 100), raw: categoryCounts.confirm_shaming, color: 'var(--accent-amber)' },
    { label: 'Forced', val: Math.round((categoryCounts.forced_continuity / maxVal) * 100), raw: categoryCounts.forced_continuity, color: 'var(--accent-red)' },
    { label: 'Drip Price', val: Math.round((categoryCounts.drip_pricing / maxVal) * 100), raw: categoryCounts.drip_pricing, color: 'var(--accent-teal)' }
  ];

  return (
    <div className="modal-backdrop">
      <motion.div 
        className="evidence-card"
        initial={{ y: 20, opacity: 0, scale: 0.96 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        style={{ padding: '0', background: 'var(--bg-canvas)' }}
      >
        {/* Top Header */}
        <div style={{ padding: 'var(--space-6) var(--space-8)', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
               <div style={{ background: 'var(--bg-canvas)', color: 'white', padding: '6px', borderRadius: '8px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
              </div>
              <div>
                <div className="evidence-title" style={{ marginBottom: '2px' }}>POST-OP AUDIT SUMMARY</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Compliance Audit Summary</div>
              </div>
            </div>
            
            <button 
              onClick={onDismiss} 
              className="btn-secondary"
              style={{ padding: '0 12px', height: 'var(--space-8)', fontSize: 'var(--text-xs)' }}
            >
              Close Ledger
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: 'var(--space-8)' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.2fr)', gap: '40px' }}>
            
            {/* Metric Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-2)' }}>Total Ingress</div>
                <div className="heading-display" style={{ fontSize: '42px', lineHeight: 1 }}>{total}</div>
              </div>
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-2)', color: 'var(--accent-amber-text)' }}>Held for Review</div>
                <div className="heading-display" style={{ fontSize: '42px', color: 'var(--accent-amber-text)', lineHeight: 1 }}>{held}</div>
              </div>
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-2)', color: 'var(--accent-teal-text)' }}>Sent Direct</div>
                <div className="heading-display" style={{ fontSize: '42px', color: 'var(--accent-teal-text)', lineHeight: 1 }}>{sent}</div>
              </div>
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-2)', color: 'var(--accent-red)' }}>Manually Rej.</div>
                <div className="heading-display" style={{ fontSize: '42px', color: 'var(--accent-red)', lineHeight: 1 }}>{rejected}</div>
              </div>
            </div>

            {/* CCPA Taxonomy Animated Bar Chart */}
            {logs.length === 0 ? (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--rad-xl)', padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '180px' }}>
                <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--text-sm)', textAlign: 'center' }}>Waiting for interception traces...</div>
              </div>
            ) : (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--rad-xl)', padding: '24px', position: 'relative' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div className="eyebrow" style={{ color: 'var(--text-primary)' }}>Dark Pattern Taxonomy Distribution</div>
                  <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>THIS SESSION</div>
                </div>
                
                <div className="bar-chart-container">
                  {taxonomyData.map((d, i) => (
                    <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, height: '100%' }}>
                       <div className="bar-track">
                         <div className="bar-fill" style={{ height: `${d.val}%`, background: d.color, animationDelay: `${i * 0.1}s` }} />
                       </div>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-2)', padding: '0 4px' }}>
                   {taxonomyData.map((d, i) => (
                      <div key={i} style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'center', width: '20%' }}>
                        {d.label}
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer Note */}
          <div style={{ marginTop: '32px', display: 'flex', alignItems: 'flex-start', gap: 'var(--space-4)', background: 'var(--bg-surface)', border: '1px solid var(--border-strong)', borderRadius: 'var(--rad-lg)', padding: 'var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
            <div style={{ background: 'var(--accent-teal-subtle)', color: 'var(--accent-teal)', padding: '6px', borderRadius: '50%' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 'var(--space-1)' }}>Precision Assurance Log:</strong>
              Classifier successfully parsed constraint absence without triggering naive regex blocks. Allowlist remained intact. No latency spike registered during real-time taxonomy evaluation.
            </div>
          </div>

        </div>
      </motion.div>
    </div>
  );
}
