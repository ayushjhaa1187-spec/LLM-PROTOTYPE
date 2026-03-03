import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                    <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
                        <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mb-6 mx-auto">
                            <svg className="w-8 h-8 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">Something went wrong</h1>
                        <p className="text-slate-600 text-center mb-8">
                            An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={() => window.location.reload()}
                                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            >
                                Reload Page
                            </button>
                            <button
                                onClick={() => window.location.href = "/"}
                                className="w-full py-3 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
                            >
                                Go to Homepage
                            </button>
                        </div>
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div className="mt-8 pt-6 border-t border-slate-100">
                                <p className="text-xs font-mono text-slate-400 break-all uppercase tracking-wider mb-2">Error Details</p>
                                <code className="text-[10px] font-mono text-rose-600 block bg-rose-50 p-2 rounded">
                                    {this.state.error.toString()}
                                </code>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
