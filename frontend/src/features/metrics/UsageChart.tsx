import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useUsageTimeSeries } from './hooks';

// Format number with k/M suffix
function formatNumber(num: number): string {
  if (num === 0) {
    return '0';
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}

export function UsageChart() {
  const { data: usageData, isLoading, error } = useUsageTimeSeries(14);
  const [pricePerMillion, setPricePerMillion] = useState('');
  const [showCost, setShowCost] = useState(false);

  if (isLoading) {
    return (
      <Card padding="lg">
        <LoadingSpinner message="Loading usage data..." />
      </Card>
    );
  }

  if (error || !usageData) {
    return (
      <Card padding="lg">
        <ErrorDisplay message="Failed to load usage data" details={error?.message} />
      </Card>
    );
  }

  const priceValue = parseFloat(pricePerMillion);

  // Format data for chart
  const chartData = usageData.map((point) => {
    const input = point.input || 0;
    const output = point.output || 0;
    const tools = point.tools || 0;
    const total = point.total || (input + output);
    const cost = showCost && !isNaN(priceValue) && priceValue > 0
      ? ((input + output) / 1_000_000) * priceValue
      : undefined;

    return {
      date: point.date,
      input,
      output,
      tools,
      total,
      cost,
      inputPercent: total > 0 ? ((input / total) * 100).toFixed(2) : '0.00',
      outputPercent: total > 0 ? ((output / total) * 100).toFixed(2) : '0.00',
    };
  });

  const handleCalculateCost = () => {
    const val = parseFloat(pricePerMillion);
    if (!isNaN(val) && val > 0) {
      setShowCost(true);
    }
  };

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPricePerMillion(e.target.value);
    if (showCost) {
      setShowCost(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div
          className="border border-anthro-border rounded-lg p-3 shadow-lg"
          style={{ backgroundColor: 'rgba(253, 252, 246, 0.98)' }}
        >
          <p className="font-medium text-anthro-text-heading mb-2">{label}</p>
          <p className="text-sm text-anthro-text-body">
            Total Tokens: <span className="font-medium">{formatNumber(data.total)}</span>
          </p>
          <div className="mt-2 space-y-1 text-xs text-anthro-text-muted">
            <p>
              <span className="inline-block w-2 h-2 rounded-full bg-[#191515] mr-1"></span>
              Input: {formatNumber(data.input)} ({data.inputPercent}%)
            </p>
            <p>
              <span className="inline-block w-2 h-2 rounded-full bg-[#D97757] mr-1"></span>
              Output: {formatNumber(data.output)} ({data.outputPercent}%)
            </p>
            <p className="flex items-center">
              <span className="inline-block w-4 h-0.5 bg-[#8E8A81] mr-1"></span>
              Tool Use: {data.tools.toLocaleString()} calls
            </p>
            {showCost && data.cost !== undefined && (
              <p className="flex items-center">
                <span className="inline-block w-4 h-0.5 bg-[#C56546] mr-1"></span>
                Cost: ${data.cost.toFixed(4)}
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const legendFormatter = (value: string) => {
    if (value === 'input') return 'Input';
    if (value === 'output') return 'Output';
    if (value === 'tools') return 'Tool Use';
    if (value === 'cost') return 'Cost ($)';
    return value;
  };

  return (
    <Card padding="lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-serif text-anthro-text-heading">Daily Token Usage</h3>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Price/M"
            value={pricePerMillion}
            onChange={handlePriceChange}
            className="w-32 px-2 py-1 text-xs border border-anthro-border rounded-lg bg-anthro-surface text-anthro-text-heading placeholder:text-anthro-text-muted focus:outline-none focus:ring-2 focus:ring-anthro-accent/30 focus:border-anthro-accent transition-colors"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCalculateCost}
            disabled={!pricePerMillion || isNaN(parseFloat(pricePerMillion)) || parseFloat(pricePerMillion) <= 0}
          >
            Calc
          </Button>
        </div>
      </div>
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: showCost ? 30 : 0, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E8E6DE" />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#8E8A81', fontSize: 12, fontFamily: 'Inter' }}
              dy={10}
            />
            <YAxis
              yAxisId="left"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#8E8A81', fontSize: 11, fontFamily: 'Inter' }}
              tickFormatter={(value) => formatNumber(value)}
              width={55}
              domain={[0, 'auto']}
              allowDataOverflow={false}
            />
            {!showCost && (
              <YAxis
                yAxisId="right"
                orientation="right"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#8E8A81', fontSize: 11, fontFamily: 'Inter' }}
                width={35}
              />
            )}
            {showCost && (
              <YAxis
                yAxisId="cost"
                orientation="right"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#C56546', fontSize: 11, fontFamily: 'Inter' }}
                tickFormatter={(value: number) => value.toFixed(2)}
                width={35}
              />
            )}
            <Tooltip cursor={{ fill: '#F5F4EF' }} content={<CustomTooltip />} />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ paddingTop: '16px', fontFamily: 'Inter', fontSize: '11px' }}
              formatter={legendFormatter}
            />
            <Bar yAxisId="left" dataKey="input" name="input" stackId="a" fill="#191515" radius={[0, 0, 4, 4]} />
            <Bar yAxisId="left" dataKey="output" name="output" stackId="a" fill="#D97757" />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="tools"
              name="tools"
              stroke="#8E8A81"
              strokeWidth={2}
              dot={{ fill: '#8E8A81', strokeWidth: 2, r: 4 }}
            />
            {showCost && (
              <Line
                yAxisId="cost"
                type="monotone"
                dataKey="cost"
                name="cost"
                stroke="#C56546"
                strokeWidth={2}
                dot={{ fill: '#C56546', strokeWidth: 2, r: 3 }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-anthro-text-muted mt-4 text-center">
        Bars show tokens (left axis) · Lines show tool calls (right axis){showCost && ' · cost ($)'}
      </p>
    </Card>
  );
}
