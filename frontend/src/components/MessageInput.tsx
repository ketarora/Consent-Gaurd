'use client';

import React, { useState, FormEvent, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MessageInputProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [content, setContent] = useState('');
  const [sending, setSending] = useState(false);
  const [microState, setMicroState] = useState<'idle' | 'parsing' | 'evaluating'>('idle');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || sending) return;

    setSending(true);
    setMicroState('parsing');
    
    // Simulate complex pipeline micro-states before resolution
    setTimeout(() => setMicroState('evaluating'), 400);

    try {
      await onSend(trimmed);
      setContent('');
    } catch (err) {
      console.error('Send failed:', err);
    } finally {
      setSending(false);
      setMicroState('idle');
    }
  };

  const canSend = content.trim() && !sending && !disabled;

  return (
    <motion.form
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.4 }}
      onSubmit={handleSubmit}
      className={`input-prompt-wrapper ${sending ? 'processing' : ''}`}
    >
      <div className="prompt-prefix" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
        agent-studio ~ %
      </div>

      <input
        className="input-prompt"
        type="text"
        placeholder="Enter message to evaluate..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        disabled={disabled || sending}
        autoComplete="off"
        spellCheck="false"
        style={{ fontFamily: 'var(--font-mono)' }}
      />

      {sending && (
        <div style={{ paddingRight: 'var(--space-3)', fontSize: 'var(--text-xs)', color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
          {microState === 'parsing' ? 'extracting_spans...' : 'running_eval_haiku_4.5...'}
        </div>
      )}

      <button
        type="submit"
        disabled={!canSend}
        className="btn-submit-arrow"
        aria-label="Intercept Message"
      >
        {sending ? (
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1.5s linear infinite' }}>
             <path d="M12 2v4"></path><path d="M12 18v4"></path><path d="M4.93 4.93l2.83 2.83"></path><path d="M16.24 16.24l2.83 2.83"></path><path d="M2 12h4"></path><path d="M18 12h4"></path><path d="M4.93 19.07l2.83-2.83"></path><path d="M16.24 7.76l2.83-2.83"></path>
           </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        )}
      </button>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .input-prompt-wrapper.processing { border-color: var(--accent-amber-subtle); box-shadow: 0 0 0 2px var(--accent-amber-subtle); }
      `}} />
    </motion.form>
  );
}
