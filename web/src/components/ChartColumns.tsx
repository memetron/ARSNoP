import { useState, useEffect, useRef } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
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

const MAX_VISIBLE_ITEMS = 6;

function ItemRow({ item }: { item: EarleyItem }) {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
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
  );
}

function ColumnCard({ column, isLatest, onSelect }: { column: EarleyColumn; isLatest: boolean; onSelect: (col: EarleyColumn) => void }) {
  const visibleItems = column.items.slice(0, MAX_VISIBLE_ITEMS);
  const remaining = column.items.length - MAX_VISIBLE_ITEMS;

  return (
    <Card
      variant="outlined"
      onClick={() => onSelect(column)}
      sx={{
        minWidth: 240,
        maxWidth: 320,
        flexShrink: 0,
        cursor: "pointer",
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
          {visibleItems.map((item, i) => (
            <ItemRow key={i} item={item} />
          ))}
        </Stack>
        {remaining > 0 && (
          <Typography sx={{ fontSize: "0.7rem", color: "text.secondary", fontStyle: "italic", mt: 0.5 }}>
            ... and {remaining} more
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export default function ChartColumns() {
  const earleyResult = useAppStore((s) => s.earleyResult);
  const currentChartColumn = useAppStore((s) => s.currentChartColumn);
  const latestRef = useRef<HTMLDivElement>(null);
  const [selectedColumn, setSelectedColumn] = useState<EarleyColumn | null>(null);

  useEffect(() => {
    latestRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "end",
    });
  }, [currentChartColumn]);

  if (!earleyResult) {
    return (
      <Typography color="text.secondary">
        Click "Parse" with the Earley variant to see the chart.
      </Typography>
    );
  }

  const visibleColumns = earleyResult.chart.slice(0, currentChartColumn + 1);

  return (
    <>
      <Box sx={{ overflowX: "auto", pb: 1 }}>
        <Stack direction="row" spacing={2}>
          {visibleColumns.map((col, i) => {
            const isLatest = i === visibleColumns.length - 1;
            return (
              <div key={col.index} ref={isLatest ? latestRef : undefined}>
                <ColumnCard column={col} isLatest={isLatest} onSelect={setSelectedColumn} />
              </div>
            );
          })}
        </Stack>
      </Box>

      <Dialog
        open={selectedColumn !== null}
        onClose={() => setSelectedColumn(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedColumn && (
          <>
            <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              Column {selectedColumn.index}
              {selectedColumn.token && ` — ${selectedColumn.token.token}: "${selectedColumn.token.lexeme}"`}
              <IconButton onClick={() => setSelectedColumn(null)} size="small">
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers>
              <Stack spacing={0.5}>
                {selectedColumn.items.map((item, i) => (
                  <ItemRow key={i} item={item} />
                ))}
              </Stack>
            </DialogContent>
          </>
        )}
      </Dialog>
    </>
  );
}
