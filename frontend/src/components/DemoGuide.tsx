'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DemoGuideProps {
  onSimulate: () => Promise<void>;
  replayLoading: boolean;
}

export default function DemoGuide({ onSimulate, replayLoading }: DemoGuideProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [completed, setCompleted] = useState<Record<number, boolean>>({});

  const toggleTask = (index: number) => {
    setCompleted(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const tasks = [
    { title: "The Safe Message", instruction: 'Type: "Here are your account details for the billing sync." (Should instantly route)' },
    { title: "The Policy Deviation", instruction: 'Type: "Confirm your order in the next 10 minutes or your cart expires forever." (Should redline & block)' },
    { title: "The Smart Allowlist", instruction: 'Type: "RideNow Cabs mandate expires tomorrow inside your PocketFund Mutual Funds account." (Should dynamically clear)' }
  ];

  useEffect(() => {
    if (Object.values(completed).filter(Boolean).length === tasks.length && isOpen) {
      const timer = setTimeout(() => setIsOpen(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [completed, isOpen, tasks.length]);

  return (
    <div style={{ position: 'fixed', bottom: '24px', left: '24px', zIndex: 50, display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            style={{
              background: 'var(--bg-glass)',
              backdropFilter: 'blur(24px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--rad-lg)',
              width: '320px',
              boxShadow: '0 24px 48px rgba(0,0,0,0.4)',
              padding: 'var(--space-4)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="accent-teal"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                Demo Checklist
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                {Object.values(completed).filter(Boolean).length} / {tasks.length}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <button
                className="btn-primary"
                onClick={() => void onSimulate()}
                disabled={replayLoading}
                style={{ justifyContent: 'center', width: '100%', background: 'var(--accent-teal)', color: 'white' }}
              >
                {replayLoading ? 'Running guided trace...' : 'Run guided demo'}
              </button>

              <AnimatePresence>
              {Object.values(completed).filter(Boolean).length === tasks.length && (
                  <motion.div initial={{opacity:0}} animate={{opacity:1}} style={{fontSize: 'var(--text-sm)', color: 'var(--accent-teal)', fontWeight: 600, textAlign: 'center', padding: 'var(--space-2) 0'}}>
                    Demo successfully completed! ✅
                  </motion.div>
              )}
              {tasks.map((task, idx) => {
                const isDone = completed[idx];
                if (isDone) return null;
                return (
                  <motion.div 
                    key={idx} 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0, overflow: 'hidden', padding: 0 }}
                    style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }} 
                    onClick={() => toggleTask(idx)}
                  >
                     <div style={{
                       width: '18px', height: '18px', borderRadius: '4px', border: `1px solid var(--border-strong)`, 
                       background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px'
                     }}>
                     </div>
                     <div style={{ cursor: 'pointer', userSelect: 'none' }}>
                        <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>{task.title}</div>
                        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{task.instruction}</div>
                     </div>
                  </motion.div>
                )
              })}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <button 
        className="btn-secondary" 
        onClick={() => setIsOpen(!isOpen)}
        style={{ alignSelf: 'flex-start', borderRadius: '100px', display: 'flex', gap: 'var(--space-2)', padding: '8px 16px', background: 'var(--bg-surface)' }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
        {isOpen ? 'Hide Guide' : 'Open Demo Guide'}
      </button>

    </div>
  );
}
