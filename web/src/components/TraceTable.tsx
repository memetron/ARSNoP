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
  if (action.type === "shift") return `Shift ${action.state}`;
  if (action.type === "reduce") {
    const p = action.production;
    return `Reduce ${p.lhs} \u2192 ${p.rhs.join(" ")}`;
  }
  return "Accept";
}

export default function TraceTable() {
  const parseResult = useAppStore((s) => s.parseResult);
  const currentTraceStep = useAppStore((s) => s.currentTraceStep);
  const setCurrentTraceStep = useAppStore((s) => s.setCurrentTraceStep);

  if (!parseResult) {
    return (
      <Typography color="text.secondary">
        Click "Parse" to see the trace.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400 }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell>Step</TableCell>
            <TableCell>Stack</TableCell>
            <TableCell>Input Buffer</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parseResult.trace.map((step) => (
            <TableRow
              key={step.step}
              hover
              selected={step.step === currentTraceStep}
              onClick={() => setCurrentTraceStep(step.step)}
              sx={{ cursor: "pointer" }}
            >
              <TableCell>{step.step}</TableCell>
              <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                [{step.stack.join(", ")}]
              </TableCell>
              <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                {step.inputBuffer.map((t) => t.lexeme).join(" ")}
              </TableCell>
              <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                {formatAction(step.action)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
