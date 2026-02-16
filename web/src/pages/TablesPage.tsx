import { Paper, Stack } from "@mui/material";
import ActionTableView from "../components/ActionTableView";
import GotoTableView from "../components/GotoTableView";

export default function TablesPage() {
  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <Stack spacing={3}>
        <ActionTableView />
        <GotoTableView />
      </Stack>
    </Paper>
  );
}
