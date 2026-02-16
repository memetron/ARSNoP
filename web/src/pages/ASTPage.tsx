import { Paper } from "@mui/material";
import ASTView from "../components/ASTView";

export default function ASTPage() {
  return (
    <Paper sx={{ p: 2 }} variant="outlined">
      <ASTView />
    </Paper>
  );
}
