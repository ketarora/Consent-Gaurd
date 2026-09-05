'use client';

import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Image from 'next/image';

import TopBar from '@/components/TopBar';
import TranscriptPanel from '@/components/TranscriptPanel';
import LedgerPanel from '@/components/LedgerPanel';
import MessageInput from '@/components/MessageInput';
import ExhibitCard from '@/components/ExhibitCard';
import AuditSummaryCard from '@/components/AuditSummaryCard';
import TechFooter from '@/components/TechFooter';

import {
  MessageWithDecision,
  AuditLogEntry,
  getMessages,
  getAuditLog,
  interceptMessage,
  approveMessage,
  rejectMessage,
  resetState,
  subscribeToEvents,
} from '@/lib/api';
import DemoGuide from '@/components/DemoGuide';
import OnboardingModal from '@/components/OnboardingModal';

const DEMO_MESSAGES = [
  "Here are your account details for the billing sync.",
  "Confirm your order in the next 10 minutes or your cart expires forever.",
  "RideNow Cabs mandate expires tomorrow due to outstanding PocketFund Mutual Funds sync.",
];

export default function ConsentGuardApp() {
  const [booting, setBooting] = useState(true);
  const [progress, setProgress] = useState(0);

  const [phase, setPhase] = useState<'landing' | 'app'>('landing');
  const [view, setView] = useState<'live' | 'log'>('live');
  
  const [messages, setMessages] = useState<MessageWithDecision[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [replayLoading, setReplayLoading] = useState(false);
  
  const [showSummary, setShowSummary] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Toast System
  const [toast, setToast] = useState<{ message: string, type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Boot Sequence
  useEffect(() => {
    const t1 = setTimeout(() => setProgress(25), 100);
    const t2 = setTimeout(() => setProgress(80), 800);
    const t3 = setTimeout(() => setProgress(100), 1200);
    const t4 = setTimeout(() => setBooting(false), 2000);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const hasSeenOnboarding = window.localStorage.getItem('consent-guard:onboarding:v1');
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  // Real-time Event Subscription (SSE)
  useEffect(() => {
    if (phase !== 'app') return;
    
    let isMounted = true;
    
    const fetchState = async () => {
      try {
        const [msgs, audit] = await Promise.all([getMessages(), getAuditLog(100)]);
        if (isMounted) {
          setMessages(msgs.reverse());
          setLogs(audit.reverse());
        }
      } catch (err) {
        console.error('Failed to fetch state:', err);
      }
    };
    
    fetchState();
    
    const unsubscribe = subscribeToEvents((eventPayload) => {
      if (isMounted) fetchState();
    });
    
    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, [phase]);

  const refreshState = async () => {
    try {
      const [msgs, audit] = await Promise.all([getMessages(), getAuditLog(100)]);
      setMessages([...msgs].reverse());
      setLogs([...audit]);
    } catch (err) {
      console.error('Failed to sync state:', err);
    }
  };

  const handleSend = async (content: string) => {
    setLoading(true);
    if (phase === 'landing') setPhase('app');
    
    try {
      await interceptMessage(content);
      await refreshState();
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    await approveMessage(id);
    showToast("Action registered: Message forwarded to destination safely.", "success");
    await refreshState();
  };

  const handleReject = async (id: string) => {
    await rejectMessage(id);
    showToast("Action registered: Message blocked — compliance rewrite suggested.", "error");
    await refreshState();
  };

  const handleReset = async () => {
    await resetState();
    setMessages([]);
    setLogs([]);
  };

  const closeOnboarding = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('consent-guard:onboarding:v1', 'seen');
    }
    setShowOnboarding(false);
  };

  const handleReplay = async () => {
    setReplayLoading(true);
    setPhase('app');
    try {
      await handleReset();
      for (const message of DEMO_MESSAGES) {
        await interceptMessage(message);
      }
      await refreshState();
    } finally {
      setReplayLoading(false);
    }
  };

  return (
    <>
      <div className={`bootloader-wrapper ${!booting ? 'loaded' : ''}`}>
        <Image src="/logo.svg" alt="Consent Guard" width={100} height={100} className="bootloader-icon" priority />
        <div className="bootloader-text">Initialize Compliance Engine</div>
        <div className="bootloader-track">
          <div className="bootloader-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
      
      <div className="app-layout" style={{ paddingBottom: '48px', position: 'relative' }}>
      <TopBar 
        view={view} 
        onViewChange={setView} 
        onReset={handleReset} 
        onReplay={handleReplay}
        onShowSummary={() => setShowSummary(true)}
        replayLoading={replayLoading}
      />

      <main style={{ flex: 1, position: 'relative' }}>
        <AnimatePresence>
          {phase === 'landing' && (
            <ExhibitCard onDismiss={() => setPhase('app')} />
          )}
        </AnimatePresence>

        <div style={{ opacity: phase === 'app' ? 1 : 0.3, filter: phase === 'app' ? 'none' : 'blur(4px)', transition: 'all 0.5s ease', pointerEvents: phase === 'app' ? 'auto' : 'none' }}>
          <div className="dashboard-grid" style={{ gridTemplateColumns: '1.4fr 1fr' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <TranscriptPanel 
                messages={messages} 
                onApprove={handleApprove} 
                onReject={handleReject} 
                loading={loading}
              />
              <MessageInput
                onSend={handleSend}
                disabled={loading || phase === 'landing'}
                quickMessages={DEMO_MESSAGES}
              />
            </div>

            <div style={{ height: 'calc(100% - 72px)' }}>
              <LedgerPanel logs={logs} />
            </div>
          </div>
        </div>
      </main>

      <AnimatePresence>
        {showSummary && (
          <AuditSummaryCard logs={logs} onDismiss={() => setShowSummary(false)} />
        )}
      </AnimatePresence>

      {phase === 'app' && <DemoGuide onSimulate={handleReplay} replayLoading={replayLoading} />}
      <OnboardingModal
        open={showOnboarding}
        onClose={closeOnboarding}
        onRunDemo={handleReplay}
        runningDemo={replayLoading}
      />

      {/* Global Toast Overlay */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.9 }}
            style={{
              position: 'fixed',
              bottom: '40px',
              left: '50%',
              x: '-50%',
              zIndex: 9999,
              background: 'var(--bg-surface-solid)',
              border: `1px solid ${toast.type === 'error' ? 'var(--flag-reject)' : 'var(--accent-teal)'}`,
              boxShadow: '0 12px 32px rgba(0,0,0,0.2)',
              padding: '12px 24px',
              borderRadius: '100px',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-base)',
              fontWeight: 500,
              color: toast.type === 'error' ? 'var(--flag-reject)' : 'var(--accent-teal)'
            }}
          >
            {toast.type === 'error' 
              ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
              : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            }
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
    </>
  );
}
