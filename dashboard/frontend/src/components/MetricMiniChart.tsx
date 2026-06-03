import { Box, Typography, useTheme } from "@mui/material";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from "recharts";

interface MetricMiniChartProps {
  title: string;
  data: { step: number; value: number }[];
  color?: string;
  height?: number;
  formatValue?: (v: number) => string;
}

export function MetricMiniChart({
  title,
  data,
  color,
  height = 100,
  formatValue = (v) => v.toFixed(4),
}: MetricMiniChartProps) {
  const theme = useTheme();
  const chartColor = color ?? theme.palette.primary.main;
  const latestValue = data.length > 0 ? data[data.length - 1].value : null;

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          mb: 0.5,
        }}
      >
        <Typography variant="body2" color="text.secondary" fontWeight={600}>
          {title}
        </Typography>
        {latestValue !== null && (
          <Typography variant="body2" fontWeight={700} color={chartColor}>
            {formatValue(latestValue)}
          </Typography>
        )}
      </Box>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis hide domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{
              background: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 6,
              fontSize: 12,
            }}
            formatter={(value: any) => [formatValue(Number(value)), title]}
            labelFormatter={(label: any) => `Epoch ${label}`}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={chartColor}
            strokeWidth={2}
            fill={`url(#grad-${title})`}
            dot={false}
            animationDuration={300}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
}
