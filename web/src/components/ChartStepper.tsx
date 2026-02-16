import { Button, Slider, Stack, Typography } from "@mui/material";
import { useAppStore } from "../store/useAppStore";

export default function ChartStepper() {
  const earleyResult = useAppStore((s) => s.earleyResult);
  const currentChartColumn = useAppStore((s) => s.currentChartColumn);
  const setCurrentChartColumn = useAppStore((s) => s.setCurrentChartColumn);

  if (!earleyResult) return null;

  const maxCol = earleyResult.chart.length - 1;

  return (
    <Stack spacing={1}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Button
          size="small"
          variant="outlined"
          disabled={currentChartColumn <= 0}
          onClick={() => setCurrentChartColumn(currentChartColumn - 1)}
        >
          Prev
        </Button>
        <Typography variant="body2" sx={{ minWidth: 100, textAlign: "center" }}>
          Column {currentChartColumn} / {maxCol}
        </Typography>
        <Button
          size="small"
          variant="outlined"
          disabled={currentChartColumn >= maxCol}
          onClick={() => setCurrentChartColumn(currentChartColumn + 1)}
        >
          Next
        </Button>
      </Stack>
      {maxCol > 0 && (
        <Slider
          value={currentChartColumn}
          min={0}
          max={maxCol}
          step={1}
          onChange={(_, val) => setCurrentChartColumn(val as number)}
          valueLabelDisplay="auto"
        />
      )}
    </Stack>
  );
}
