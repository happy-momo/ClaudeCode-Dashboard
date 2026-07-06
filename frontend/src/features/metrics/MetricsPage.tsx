import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { UsageChart } from './UsageChart';
import { useContextWindow } from './hooks';

// Format number with k/M suffix
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}

const CONTEXT_CARD_HEIGHT = '140px'; // Compact height for context window card
const CHART_HEIGHT = '280px'; // Chart height to match overall page height
const CONTENT_MIN_HEIGHT = '520px'; // Fixed min height to match other pages

export function ContextWindowCard() {
  const { data: contextWindow, isLoading, error } = useContextWindow();

  if (isLoading) {
    return (
      <Card padding="lg" style={{ minHeight: CONTEXT_CARD_HEIGHT }}>
        <LoadingSpinner message="Loading context window..." />
      </Card>
    );
  }

  if (error || !contextWindow) {
    return (
      <Card padding="lg" style={{ minHeight: CONTEXT_CARD_HEIGHT }}>
        <ErrorDisplay
          message="Failed to load context window"
          details={error?.message}
        />
      </Card>
    );
  }

  const inputTokens = contextWindow.input_tokens ?? contextWindow.inputTokens ?? 0;
  const outputTokens = contextWindow.output_tokens ?? contextWindow.outputTokens ?? 0;
  const toolCalls = contextWindow.tool_calls ?? contextWindow.toolCalls ?? 0;
  const totalTokens = inputTokens + outputTokens;
  const sessionId = contextWindow.session_id || 'default';

  return (
    <Card padding="lg">
      <div className="flex justify-between items-end mb-3">
        <div>
          <h3 className="text-base font-serif text-anthro-text-heading">Current Session</h3>
          <p className="text-xs text-anthro-text-muted mt-0.5 font-mono truncate max-w-[200px]">
            {sessionId}
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-serif text-anthro-text-heading tracking-tight">
            {formatNumber(contextWindow.used)}
          </span>
          <span className="text-anthro-text-muted ml-2 text-xs font-medium">
            input
          </span>
        </div>
      </div>

      {/* Billable token consumption - Compact horizontal layout */}
      <div className="pt-3 border-t border-anthro-border">
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-anthro-bg rounded-lg">
            <div className="text-lg font-serif text-anthro-text-heading">
              {formatNumber(inputTokens)}
            </div>
            <div className="text-xs text-anthro-text-muted mt-0.5">Input</div>
          </div>
          <div className="text-center p-2 bg-anthro-bg rounded-lg">
            <div className="text-lg font-serif text-anthro-text-heading">
              {formatNumber(outputTokens)}
            </div>
            <div className="text-xs text-anthro-text-muted mt-0.5">Output</div>
          </div>
          <div className="text-center p-2 bg-anthro-bg rounded-lg">
            <div className="text-lg font-serif text-anthro-text-heading">
              {toolCalls.toLocaleString()}
            </div>
            <div className="text-xs text-anthro-text-muted mt-0.5">Tools</div>
          </div>
        </div>
      </div>
    </Card>
  );
}

export function MetricsPage() {
  return (
    <div className="space-y-4 animate-in fade-in duration-500" style={{ minHeight: CONTENT_MIN_HEIGHT }}>
      {/* Page Header */}
      <div className="shrink-0">
        <h2 className="text-3xl font-serif text-anthro-text-heading tracking-tight">
          Metrics
        </h2>
        <p className="text-anthro-text-body text-sm mt-1 font-medium">
          Token usage and context window statistics
        </p>
      </div>

      {/* Top Row: Current Session Stats */}
      <div className="shrink-0">
        <ContextWindowCard />
      </div>

      {/* Bottom Row: Historical Usage Chart */}
      <div className="shrink-0">
        <UsageChart />
      </div>
    </div>
  );
}