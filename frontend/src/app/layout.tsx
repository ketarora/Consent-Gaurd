import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Consent Guard — AI Commerce Compliance Layer',
  description: 'Real-time governance layer that intercepts, classifies, and audits AI agent messages for India CCPA 2023 dark-pattern categories before they reach customers.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <meta name="theme-color" content="#FAFAFA" />
      </head>
      <body>{children}</body>
    </html>
  );
}
