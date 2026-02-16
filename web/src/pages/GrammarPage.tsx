import { Paper } from "@mui/material";
import GrammarPanel from "../components/GrammarPanel";

export default function GrammarPage() {
  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <GrammarPanel />
    </Paper>
  );
}
