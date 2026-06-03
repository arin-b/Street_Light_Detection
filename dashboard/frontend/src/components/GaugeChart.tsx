import { Box, Typography, useTheme } from "@mui/material";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

interface GaugeChartProps {
  label: string;
  value: number; // 0-100
  color?: string;
  size?: number;
  subtitle?: string;
}

export function GaugeChart({
  label,
  value,
  color,
  size = 140,
  subtitle,
}: GaugeChartProps) {
  const theme = useTheme();

  // Dynamic color based on value if not provided
  const gaugeColor =
    color ??
    (value > 90
      ? theme.palette.error.main
      : value > 70
        ? theme.palette.warning.main
        : theme.palette.success.main);

  const bgColor = theme.palette.action.hover;

  const data = [
    { name: "used", value: Math.min(value, 100) },
    { name: "free", value: Math.max(100 - value, 0) },
  ];

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
      }}
    >
      <Box sx={{ width: size, height: size, position: "relative" }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="90%"
              startAngle={90}
              endAngle={-270}
              dataKey="value"
              strokeWidth={0}
              animationDuration={500}
            >
              <Cell fill={gaugeColor} />
              <Cell fill={bgColor} />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          <Typography
            variant="h6"
            fontWeight={800}
            sx={{ lineHeight: 1.1, color: gaugeColor }}
          >
            {value.toFixed(0)}%
          </Typography>
        </Box>
      </Box>
      <Typography
        variant="body2"
        fontWeight={700}
        sx={{ mt: 0.5, textAlign: "center" }}
      >
        {label}
      </Typography>
      {subtitle && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ textAlign: "center" }}
        >
          {subtitle}
        </Typography>
      )}
    </Box>
  );
}
