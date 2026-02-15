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

export default function GotoTableView() {
  const tablesResult = useAppStore((s) => s.tablesResult);

  if (!tablesResult) {
    return (
      <Typography color="text.secondary">
        Generate tables first.
      </Typography>
    );
  }

  const nonTerminals = new Set<string>();
  Object.values(tablesResult.gotoTable).forEach((row) => {
    Object.keys(row).forEach((nt) => nonTerminals.add(nt));
  });
  const cols = [...nonTerminals].sort();

  const stateKeys = Object.keys(tablesResult.gotoTable)
    .sort((a, b) => Number(a) - Number(b));

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ overflowX: "auto" }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: "bold", minWidth: 60 }}>State</TableCell>
            {cols.map((nt) => (
              <TableCell
                key={nt}
                align="center"
                sx={{ fontFamily: "monospace", fontWeight: "bold", minWidth: 80 }}
              >
                {nt}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {stateKeys.map((stateKey) => (
            <TableRow key={stateKey} hover>
              <TableCell sx={{ fontWeight: "bold" }}>{stateKey}</TableCell>
              {cols.map((nt) => {
                const val = tablesResult.gotoTable[stateKey]?.[nt];
                return (
                  <TableCell
                    key={nt}
                    align="center"
                    sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                  >
                    {val !== undefined ? val : ""}
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
