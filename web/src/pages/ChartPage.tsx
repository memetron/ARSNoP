import { Paper, Stack } from "@mui/material";
import ChartStepper from "../components/ChartStepper";
import ChartColumns from "../components/ChartColumns";

export default function ChartPage() {
  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <Stack spacing={3}>
        <ChartStepper />
        <ChartColumns />
      </Stack>
    </Paper>
  );
}
