import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import type { Action } from "../api/types";

function formatAction(action: Action): string {
  if (action.type === "shift") return `s${action.state}`;
  if (action.type === "reduce") {
    const p = action.production;
    return `r(${p.lhs}\u2192${p.rhs.join(" ")})`;
  }
  return "acc";
}

function actionColor(action: Action): string {
  if (action.type === "shift") return "#1565c0";
  if (action.type === "reduce") return "#2e7d32";
  return "#f9a825";
}

export default function ActionTableView() {
  const tablesResult = useAppStore((s) => s.tablesResult);

  if (!tablesResult) {
    return (
      <Typography color="text.secondary">
        Generate tables first.
      </Typography>
    );
  }

  // Collect all terminal columns from the action table
  const terminals = new Set<string>();
  Object.values(tablesResult.actionTable).forEach((row) => {
    Object.keys(row).forEach((t) => terminals.add(t));
  });
  const terminalList = [...terminals].sort();
  // Move "$" to end
  const cols = terminalList.filter((t) => t !== "$").concat(
    terminalList.includes("$") ? ["$"] : []
  );

  const stateKeys = Object.keys(tablesResult.actionTable)
    .sort((a, b) => Number(a) - Number(b));

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ overflowX: "auto" }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: "bold", minWidth: 60 }}>State</TableCell>
            {cols.map((t) => (
              <TableCell
                key={t}
                align="center"
                sx={{ fontFamily: "monospace", fontWeight: "bold", minWidth: 80 }}
              >
                {t}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {stateKeys.map((stateKey) => (
            <TableRow key={stateKey} hover>
              <TableCell sx={{ fontWeight: "bold" }}>{stateKey}</TableCell>
              {cols.map((t) => {
                const action = tablesResult.actionTable[stateKey]?.[t];
                return (
                  <TableCell
                    key={t}
                    align="center"
                    sx={{
                      fontFamily: "monospace",
                      fontSize: "0.8rem",
                      color: action ? actionColor(action) : undefined,
                      fontWeight: action ? "bold" : undefined,
                    }}
                  >
                    {action ? formatAction(action) : ""}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
