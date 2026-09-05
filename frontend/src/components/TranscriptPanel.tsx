'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageWithDecision } from '../lib/api';

interface TranscriptPanelProps {
  messages: MessageWithDecision[];
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  loading?: boolean;
}

export default function TranscriptPanel({ messages, onApprove, onReject, loading }: TranscriptPanelProps) {
  
  // Highlight flagged spans with dynamic strikethrough/badges using Case-Insensitive safe Regex
  const renderContent = (msg: MessageWithDecision) => {
    if (!msg.decision || !msg.decision.flags || msg.decision.flags.length === 0) {
      return msg.content;
    }

    const activeFlags = msg.decision.flags.filter(f => !f.cleared_by_allowlist);
    if (activeFlags.length === 0) return msg.content;

    // Build a safe regex pattern escaping special characters
    const patterns = activeFlags
      .map(f => f.quoted_span.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .filter(Boolean);

    if (patterns.length === 0) return msg.content;

    const regex = new RegExp(`(${patterns.join('|')})`, 'gi');
    const parts = msg.content.split(regex);

    const isRejected = msg.decision.action === 'rejected';
    const isApproved = msg.decision.action === 'approved';

    return parts.map((part, idx) => {
      const matchedFlag = activeFlags.find(
        f => f.quoted_span.toLowerCase() === part.toLowerCase()
      );

      if (matchedFlag) {
        let badgeClass = 'flag-amber';
        if (isRejected) badgeClass = 'flag-red';
        if (isApproved) badgeClass = 'flag-teal';

        return (
          <React.Fragment key={idx}>
            <span className={`redline-span ${isRejected ? 'is-rejected' : ''}`}>
              {part}
            </span>
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`flag-badge ${badgeClass}`}
              style={{ marginLeft: '4px', verticalAlign: 'middle' }}
            >
              § {matchedFlag.category.replace(/_/g, ' ').toUpperCase()} ({Math.round(matchedFlag.confidence * 100)}%)
            </motion.span>
          </React.Fragment>
        );
      }
      return part;
    });
  };

  return (
    <div className="panel transcript-area">
      {messages.length === 0 && !loading && (
        <div style={{ padding: 'var(--space-8)' }}>
          <h2 style={{ fontFamily: 'var(--font-display)', margin: '0 0 var(--space-2) 0', fontSize: 'var(--text-lg)' }}>🚀 Evaluator's Demo Guide</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-6)', fontSize: 'var(--text-base)' }}>
            To test the Consent Guard compliance firewall, paste these exact phrases into the terminal below:
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div style={{ background: 'var(--bg-surface)', padding: 'var(--space-4)', borderRadius: 'var(--rad-lg)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--accent-teal)', marginBottom: 'var(--space-1)' }}>TEST 1: THE SAFE MESSAGE</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                "Here are your account details for the billing sync."
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Expected: Instantly passes with no friction.</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: 'var(--space-4)', borderRadius: 'var(--rad-lg)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--accent-red)', marginBottom: 'var(--space-1)' }}>TEST 2: THE CCPA MANIPULATION</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                "Confirm your order in the next 10 minutes or your cart expires forever."
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Expected: Regex catches trigger → LLM verifies forced urgency → Route dropped & Redlined.</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: 'var(--space-4)', borderRadius: 'var(--rad-lg)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--accent-amber-text)', marginBottom: 'var(--space-1)' }}>TEST 3: THE SMART ALLOWLIST</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                "RideNow Cabs mandate expires tomorrow due to outstanding PocketFund Mutual Funds sync."
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Expected: System recognizes 'PocketFund Mutual Funds', confirms a real DB mandate exists, and clears it.</div>
            </div>
          </div>
        </div>
      )}

      {messages.map((msg) => {
        const isAgent = !!msg.agent_id;
        
        return (
          <div key={msg.id} className="msg-entry">
            {/* Avatars Removed per Forensic Audit (Severity 5) — Enforcing strict compliance text presentation */}

            <div className="msg-content-block">
              <div className="msg-meta">
                <span className="msg-agent-tag">{isAgent ? `@${msg.agent_id}` : 'Human Operator'}</span>
                <span className="msg-timestamp">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
              </div>
              
              <div className={`msg-body-text ${msg.decision?.action === 'held' ? 'msg-scanning' : ''}`}>
                {renderContent(msg)}
                
                {/* SVG Stamp Injection */}
                <svg className={`stamp-overlay ${msg.decision?.action === 'rejected' ? 'active' : ''}`} width="100" height="40" viewBox="0 0 100 40">
                  <rect x="2" y="2" width="96" height="36" rx="4" fill="none" stroke="var(--flag-reject)" strokeWidth="3" strokeDasharray="6 2" opacity="0.8"/>
                  <text x="50" y="26" fontSize="18" fontWeight="bold" fontFamily="var(--font-display)" fill="var(--flag-reject)" textAnchor="middle" letterSpacing="2">REJECTED</text>
                </svg>
                
                <svg className={`stamp-overlay ${msg.decision?.action === 'approved' ? 'active' : ''}`} width="100" height="40" viewBox="0 0 100 40">
                  <rect x="2" y="2" width="96" height="36" rx="4" fill="none" stroke="var(--accent-teal)" strokeWidth="3" strokeDasharray="6 2" opacity="0.8"/>
                  <text x="50" y="26" fontSize="18" fontWeight="bold" fontFamily="var(--font-display)" fill="var(--accent-teal)" textAnchor="middle" letterSpacing="2">APPROVED</text>
                </svg>
              </div>

              <AnimatePresence>
                {msg.decision?.action === 'held' && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    style={{ overflow: 'hidden' }}
                  >
                    <div className="review-actions">
                      <button className="btn-primary" onClick={() => onApprove(msg.id)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        Approve
                      </button>
                      <button className="btn-danger" onClick={() => onReject(msg.id)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        Reject
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Post-Action Feedback (Suggested Rewrite) */}
              <AnimatePresence>
                {msg.decision?.action === 'rejected' && msg.decision?.flags?.some(f => f.suggested_rewrite) && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0, y: -10 }}
                    animate={{ height: 'auto', opacity: 1, y: 0 }}
                    transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                    style={{ overflow: 'hidden', marginTop: 'var(--space-3)' }}
                  >
                    <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-strong)', borderRadius: 'var(--rad-md)', padding: '12px 14px', fontSize: 'var(--text-sm)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 'var(--space-1)', textTransform: 'uppercase', fontSize: 'var(--text-xs)', letterSpacing: '0.05em', display: 'flex', gap: 'var(--space-1)', alignItems: 'center' }}>
                         <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                        Compliant Rewrite Suggested
                      </div>
                      <div style={{ color: 'var(--text-primary)', fontStyle: 'italic', fontFamily: 'var(--font-body)' }}>
                        "{msg.decision.flags.find(f => f.suggested_rewrite)?.suggested_rewrite}"
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Post-Action Feedback (Cleared/Forwarded) */}
              <AnimatePresence>
                {msg.decision?.action === 'approved' && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0, y: -10 }}
                    animate={{ height: 'auto', opacity: 1, y: 0 }}
                    transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                    style={{ overflow: 'hidden', marginTop: 'var(--space-3)' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--accent-teal)', fontSize: 'var(--text-xs)', fontWeight: 600, background: 'var(--accent-teal-subtle)', padding: '8px 12px', borderRadius: 'var(--rad-md)' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      MESSAGE FORWARDED TO DESTINATION
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        );
      })}
    </div>
  );
}
