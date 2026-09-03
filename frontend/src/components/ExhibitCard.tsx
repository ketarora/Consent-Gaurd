'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ExhibitCardProps {
  onDismiss: () => void;
}

export default function ExhibitCard({ onDismiss }: ExhibitCardProps) {
  // A raw JSON payload visualization wrapper
  const payloadString = `{
  "agent_id": "demo-agent-01",
  "intent": "collect_mandate",
  "payload": "Hi there! I created a UPI mandate for your SIP. Please authorise it, it expires in 2 hours!",
  "timestamp": "${new Date().toISOString()}"
}`;

  return (
    <div className="modal-backdrop">
      <motion.div 
        className="landing-card"
        initial={{ y: 20, opacity: 0, scale: 0.95, rotateX: 10 }}
        animate={{ y: 0, opacity: 1, scale: 1, rotateX: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        style={{ perspective: '1000px', transformStyle: 'preserve-3d', padding: '0', background: 'var(--bg-canvas)' }}
      >
        <div style={{ padding: 'var(--space-8) var(--space-8) var(--space-4)', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', padding: '6px', borderRadius: '8px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              </div>
              <h1 style={{ margin: 0 }}>Consent Guard Core</h1>
            </div>
            
            <button 
              onClick={onDismiss} 
              className="btn-secondary"
              style={{ border: 'none', background: 'transparent', padding: '4px' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          <p style={{ margin: 0, fontSize: 'var(--text-base)' }}>
            AI agents operate within numeric limits, but lack guardrails on <em>phrasing</em>. 
            Consent Guard evaluates outbound packets against India's CCPA Dark Pattern Taxonomy before delivery.
          </p>
        </div>

        {/* Technical JSON Payload view */}
        <div style={{ padding: 'var(--space-6) var(--space-8)', borderTop: '1px solid var(--border-subtle)' }}>
          <div className="evidence-title">
            INTERCEPTED EXFILTRATION (EXHIBIT A)
          </div>
          <div style={{ 
            background: 'var(--bg-canvas)', 
            color: 'var(--text-primary)', 
            padding: 'var(--space-4)', 
            borderRadius: 'var(--rad-lg)', 
            fontFamily: 'var(--font-mono)', 
            fontSize: 'var(--text-xs)',
            lineHeight: 1.6,
            overflowX: 'hidden'
          }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              <span style={{ color: 'var(--flag-reject)' }}>{"{"}</span>{'\n'}
              {'  '}<span style={{ color: 'var(--accent-blue)' }}>"agent_id"</span>: <span style={{ color: 'var(--accent-teal)' }}>"demo-agent-01"</span>,{'\n'}
              {'  '}<span style={{ color: 'var(--accent-blue)' }}>"intent"</span>: <span style={{ color: 'var(--accent-teal)' }}>"collect_mandate"</span>,{'\n'}
              {'  '}<span style={{ color: 'var(--accent-blue)' }}>"message"</span>: <span style={{ color: 'var(--accent-teal)' }}>"Hi there! I created a UPI mandate for your SIP. Please authorise it, <span style={{ background: 'var(--accent-amber-subtle)', color: 'var(--accent-amber-text)', padding: '0 2px' }}>it expires in 2 hours!</span>"</span>{'\n'}
              <span style={{ color: 'var(--flag-reject)' }}>{"}"}</span>
            </pre>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', padding: 'var(--space-4) var(--space-8) var(--space-8)' }}>
          <button className="btn-primary" onClick={onDismiss}>
            Initialize Governance Audit →
          </button>
        </div>
      </motion.div>
    </div>
  );
}
