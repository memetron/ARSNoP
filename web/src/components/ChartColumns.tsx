import {
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import type { EarleyItem, EarleyColumn } from "../api/types";

const OPERATION_COLOR: Record<string, "info" | "warning" | "primary" | "success"> = {
  init: "info",
  predict: "warning",
  scan: "primary",
  complete: "success",
};

function formatItem(item: EarleyItem): string {
  const { lhs, rhs } = item.production;
  const before = rhs.slice(0, item.dot).join(" ");
  const after = rhs.slice(item.dot).join(" ");
  return `${lhs} \u2192 ${before} \u2022 ${after}`;
}

function ColumnCard({ column, isLatest }: { column: EarleyColumn; isLatest: boolean }) {
  return (
    <Card
      variant="outlined"
      sx={{
        minWidth: 240,
        maxWidth: 320,
        flexShrink: 0,
        borderColor: isLatest ? "primary.main" : "divider",
        borderWidth: isLatest ? 2 : 1,
      }}
    >
      <CardContent sx={{ py: 1, "&:last-child": { pb: 1 } }}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" fontWeight="bold">
            Column {column.index}
          </Typography>
          {column.token && (
            <Chip
              label={`${column.token.token}: "${column.token.lexeme}"`}
              size="small"
              variant="outlined"
            />
          )}
        </Stack>
        <Stack spacing={0.5}>
          {column.items.map((item, i) => (
            <Stack key={i} direction="row" spacing={1} alignItems="center">
              <Chip
                label={item.operation}
                size="small"
                color={OPERATION_COLOR[item.operation] ?? "default"}
                sx={{ minWidth: 72, fontWeight: 500 }}
              />
              <Typography
                variant="body2"
                sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              >
                {formatItem(item)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ({item.origin})
              </Typography>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function ChartColumns() {
  const earleyResult = useAppStore((s) => s.earleyResult);
  const currentChartColumn = useAppStore((s) => s.currentChartColumn);

  if (!earleyResult) {
    return (
      <Typography color="text.secondary">
        Click "Parse" with the Earley variant to see the chart.
      </Typography>
    );
  }

  const visibleColumns = earleyResult.chart.slice(0, currentChartColumn + 1);

  return (
    <Box sx={{ overflowX: "auto", pb: 1 }}>
      <Stack direction="row" spacing={2}>
        {visibleColumns.map((col, i) => (
          <ColumnCard
            key={col.index}
            column={col}
            isLatest={i === visibleColumns.length - 1}
          />
        ))}
      </Stack>
    </Box>
  );
}
