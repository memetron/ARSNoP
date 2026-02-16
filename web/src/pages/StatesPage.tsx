import { useState } from "react";
import { Paper, ToggleButton, ToggleButtonGroup, Box } from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import StateGraph from "../components/StateGraph";
import StateList from "../components/StateList";

export default function StatesPage() {
  const [view, setView] = useState<"graph" | "list">("graph");

  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <Box sx={{ mb: 2, display: "flex", justifyContent: "flex-end" }}>
        <ToggleButtonGroup
          value={view}
          exclusive
          onChange={(_, val) => { if (val) setView(val); }}
          size="small"
        >
          <ToggleButton value="graph">
            <AccountTreeIcon sx={{ mr: 0.5 }} fontSize="small" />
            Graph
          </ToggleButton>
          <ToggleButton value="list">
            <ViewListIcon sx={{ mr: 0.5 }} fontSize="small" />
            List
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {view === "graph" ? <StateGraph /> : <StateList />}
    </Paper>
  );
}
