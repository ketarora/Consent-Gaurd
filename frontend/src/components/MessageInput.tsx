'use client';

import React, { useState, FormEvent, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MessageInputProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
  quickMessages?: string[];
}

export default function MessageInput({ onSend, disabled, quickMessages = [] }: MessageInputProps) {
  const [content, setContent] = useState('');
  const [sending, setSending] = useState(false);
  const [microState, setMicroState] = useState<'idle' | 'parsing' | 'evaluating'>('idle');

  const sendMessage = async (message: string, clearInput: boolean) => {
    setSending(true);
    setMicroState('parsing');

    setTimeout(() => setMicroState('evaluating'), 400);

    try {
      await onSend(message);
      if (clearInput) {
        setContent('');
      }
    } catch (err) {
      console.error('Send failed:', err);
    } finally {
      setSending(false);
      setMicroState('idle');
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || sending) return;
    await sendMessage(trimmed, true);
  };

  const canSend = content.trim() && !sending && !disabled;

  return (
    <motion.form
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.4 }}
      onSubmit={handleSubmit}
      className={`input-prompt-wrapper ${sending ? 'processing' : ''}`}
      style={{ position: 'relative' }}
    >
      <div style={{ position: 'absolute', top: '-42px', left: '16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button type="button" className="preset-chip" onClick={() => void sendMessage("Confirm your order in the next 10 minutes or your cart expires forever.", false)} disabled={disabled || sending}>
          <span className="chip-icon">🔴</span> Test 1: False Urgency (FTX'26)
        </button>
        <button type="button" className="preset-chip" onClick={() => void sendMessage("Scheduled mandate renewal notice due tomorrow.", false)} disabled={disabled || sending}>
          <span className="chip-icon">🟢</span> Test 2: Legit Expiry (Allowlist Override)
        </button>
        <button type="button" className="preset-chip" onClick={() => void sendMessage("Keep my Premium plan, or click here if you hate saving money.", false)} disabled={disabled || sending}>
          <span className="chip-icon">🟡</span> Test 3: Confirm Shaming
        </button>
        <button type="button" className="preset-chip" onClick={() => void sendMessage("We've added a travel insurance to your checkout for just 20 bucks.", false)} disabled={disabled || sending}>
          <span className="chip-icon">🟣</span> Test 4: Basket Sneaking
        </button>
      </div>

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
        .preset-chip {
          background: rgba(255,255,255,0.7); border: 1px solid var(--border-strong);
          padding: 6px 12px; border-radius: 999px; font-size: 11px; font-weight: 600;
          color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
          display: flex; align-items: center; gap: 6px; box-shadow: var(--shadow-sm);
        }
        .preset-chip:hover:not(:disabled) { background: #fff; transform: translateY(-1px); box-shadow: var(--shadow-md); color: var(--text-primary); }
        .preset-chip:disabled { opacity: 0.5; cursor: not-allowed; }
        .chip-icon { font-size: 12px; }
      `}} />
    </motion.form>
  );
}
