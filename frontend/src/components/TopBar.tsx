'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface TopBarProps {
  view: 'live' | 'log';
  onViewChange: (view: 'live' | 'log') => void;
  onReset: () => void;
  onReplay: () => void;
  onShowSummary: () => void;
  replayLoading?: boolean;
}

export default function TopBar({ view, onViewChange, onReset, onReplay, onShowSummary, replayLoading }: TopBarProps) {
  const exportCSV = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/audit-log`, '_blank');
  };

  return (
    <motion.header
      className="header-glass"
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Brand & Classifier Info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <div className="brand-mark">
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'var(--text-lg)', color: 'var(--text-primary)', letterSpacing: '-0.02em', borderBottom: '2px solid var(--accent-red)' }}>Consent Guard</span>
        </div>

        <div style={{ width: '1px', height: 'var(--space-4)', background: 'var(--border-strong)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div className="status-indicator">
            <span className="status-dot" />
            <span className="text-mono" style={{ fontSize: 'var(--text-xs)', letterSpacing: '0.02em' }}>Classifier: Claude Haiku 4.5</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <button 
          className="btn-secondary" 
          onClick={onReplay} 
          disabled={replayLoading}
          style={{ 
            height: 'var(--space-7)', fontSize: 'var(--text-xs)', padding: '0 10px', 
            background: 'var(--accent-amber-subtle)', 
            borderColor: 'transparent',
            color: 'var(--accent-amber-text)' 
          }}
        >
          {replayLoading ? 'REPLAYING TRACE...' : 'REPLAY: FTX\'26'}
        </button>

        <button 
          className="btn-secondary" 
          onClick={exportCSV} 
          style={{ height: 'var(--space-7)', fontSize: 'var(--text-xs)', padding: '0 10px' }}
        >
          EXPORT AUDIT (.JSONL)
        </button>

        <button 
          className="btn-secondary" 
          onClick={onShowSummary}
          style={{ height: 'var(--space-7)', fontSize: 'var(--text-xs)', padding: '0 10px' }}
        >
          METRICS
        </button>
        
        <button 
          className="btn-secondary" 
          onClick={onReset}
          style={{ height: 'var(--space-7)', fontSize: 'var(--text-xs)', padding: '0 10px' }}
        >
          RESET TRACE
        </button>
      </div>
    </motion.header>
  );
}
