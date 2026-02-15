import {
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Stack,
  Box,
} from "@mui/material";
import { useAppStore } from "../store/useAppStore";

export default function GrammarInfo() {
  const analysis = useAppStore((s) => s.grammarAnalysis);

  if (!analysis) {
    return (
      <Typography color="text.secondary">
        Click "Analyze" to see grammar info.
      </Typography>
    );
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Terminals
        </Typography>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {analysis.terminals.map((t) => (
            <Chip key={t} label={t} size="small" color="primary" variant="outlined" />
          ))}
        </Stack>
      </Box>

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Non-Terminals
        </Typography>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {analysis.nonTerminals.map((nt) => (
            <Chip key={nt} label={nt} size="small" color="secondary" variant="outlined" />
          ))}
        </Stack>
      </Box>

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Productions
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Production</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analysis.productions.map((p, i) => (
                <TableRow key={i}>
                  <TableCell>{i}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace" }}>
                    {p.lhs} &rarr; {p.rhs.join(" ")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          FIRST Sets
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Non-Terminal</TableCell>
                <TableCell>FIRST</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(analysis.firstSets).map(([nt, firsts]) => (
                <TableRow key={nt}>
                  <TableCell sx={{ fontFamily: "monospace" }}>{nt}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                      {firsts.map((f) => (
                        <Chip key={f} label={f} size="small" />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          FOLLOW Sets
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Non-Terminal</TableCell>
                <TableCell>FOLLOW</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(analysis.followSets).map(([nt, follows]) => (
                <TableRow key={nt}>
                  <TableCell sx={{ fontFamily: "monospace" }}>{nt}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                      {follows.map((f) => (
                        <Chip key={f} label={f} size="small" />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Stack>
  );
}
