import { Paper, Stack } from "@mui/material";
import TraceDebugger from "../components/TraceDebugger";
import TraceTable from "../components/TraceTable";

export default function TracePage() {
  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <Stack spacing={3}>
        <TraceDebugger />
        <TraceTable />
      </Stack>
    </Paper>
  );
}
