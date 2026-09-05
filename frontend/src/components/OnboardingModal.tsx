'use client';

import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface OnboardingModalProps {
  open: boolean;
  onClose: () => void;
  onRunDemo: () => Promise<void>;
  runningDemo: boolean;
}

export default function OnboardingModal({ open, onClose, onRunDemo, runningDemo }: OnboardingModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div
            className="landing-card"
            initial={{ y: 18, opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 16, opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            style={{ maxWidth: '560px', padding: '24px' }}
          >
            <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: '8px' }}>Quick Demo Onboarding</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Use one-click simulation to show hold/review/release flow, then inspect the audit ledger.
            </p>
            <ol style={{ margin: '0 0 20px 20px', color: 'var(--text-secondary)', display: 'grid', gap: '8px' }}>
              <li>Click <strong>Run guided demo</strong> to generate a realistic trace.</li>
              <li>Use <strong>Approve</strong> or <strong>Reject</strong> on held messages.</li>
              <li>Use <strong>Simulate 1/2/3</strong> chips for one-off examples.</li>
            </ol>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" type="button" onClick={onClose}>
                Skip for now
              </button>
              <button
                className="btn-primary"
                type="button"
                disabled={runningDemo}
                onClick={() => void onRunDemo().finally(onClose)}
              >
                {runningDemo ? 'Running…' : 'Run guided demo'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
