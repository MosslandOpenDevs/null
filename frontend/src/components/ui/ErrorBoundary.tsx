"use client";

import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[200px] gap-4 p-6">
          <div className="font-mono text-base text-glow-red accent-glow">
            A DISTURBANCE IN THE VOID
          </div>
          <div className="font-mono text-sm text-hud-muted text-center max-w-md">
            {this.state.error?.message || "An unexpected error occurred"}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="font-mono text-sm text-accent border border-accent/30 px-4 py-2 hover:bg-accent/10 transition-colors uppercase tracking-wider"
          >
            RETRY
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
