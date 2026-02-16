import {
  Box,
  Chip,
  IconButton,
  Slider,
  Stack,
  Typography,
} from "@mui/material";
import SkipPreviousIcon from "@mui/icons-material/SkipPrevious";
import SkipNextIcon from "@mui/icons-material/SkipNext";
import { useAppStore } from "../store/useAppStore";
import type { Action } from "../api/types";

function formatAction(action: Action): string {
  if (action.type === "shift") return `Shift to state ${action.state}`;
  if (action.type === "reduce") {
    const p = action.production;
    return `Reduce by ${p.lhs} \u2192 ${p.rhs.join(" ")}`;
  }
  return "Accept!";
}

export default function TraceDebugger() {
  const parseResult = useAppStore((s) => s.parseResult);
  const currentTraceStep = useAppStore((s) => s.currentTraceStep);
  const setCurrentTraceStep = useAppStore((s) => s.setCurrentTraceStep);

  if (!parseResult || parseResult.trace.length === 0) {
    return (
      <Typography color="text.secondary">
        No trace available.
      </Typography>
    );
  }

  const maxStep = parseResult.trace.length - 1;
  const step = parseResult.trace[currentTraceStep];
  const currentState = step.stack[step.stack.length - 1];

  return (
    <Stack spacing={2}>
      {/* Controls */}
      <Stack direction="row" alignItems="center" spacing={1}>
        <IconButton
          onClick={() => setCurrentTraceStep(Math.max(0, currentTraceStep - 1))}
          disabled={currentTraceStep === 0}
          size="small"
        >
          <SkipPreviousIcon />
        </IconButton>
        <Box sx={{ flex: 1, px: 2 }}>
          <Slider
            value={currentTraceStep}
            min={0}
            max={maxStep}
            step={1}
            onChange={(_, val) => setCurrentTraceStep(val as number)}
            valueLabelDisplay="auto"
          />
        </Box>
        <IconButton
          onClick={() => setCurrentTraceStep(Math.min(maxStep, currentTraceStep + 1))}
          disabled={currentTraceStep === maxStep}
          size="small"
        >
          <SkipNextIcon />
        </IconButton>
        <Typography variant="body2" color="text.secondary" sx={{ minWidth: 60 }}>
          {currentTraceStep}/{maxStep}
        </Typography>
      </Stack>

      {/* Current State */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Current State
        </Typography>
        <Chip
          label={`State ${currentState}`}
          color="info"
          sx={{ fontWeight: "bold", fontSize: "0.9rem" }}
        />
      </Box>

      {/* Stack */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Stack
        </Typography>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {step.stack.map((s, i) => (
            <Chip
              key={i}
              label={s}
              size="small"
              variant={i === step.stack.length - 1 ? "filled" : "outlined"}
              color={i === step.stack.length - 1 ? "info" : "default"}
            />
          ))}
        </Stack>
      </Box>

      {/* Input Buffer */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Input Buffer
        </Typography>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {step.inputBuffer.map((t, i) => (
            <Chip
              key={i}
              label={`${t.lexeme} (${t.token})`}
              size="small"
              color={i === 0 ? "primary" : "default"}
              variant={i === 0 ? "filled" : "outlined"}
            />
          ))}
        </Stack>
      </Box>

      {/* Action */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Action
        </Typography>
        <Chip
          label={formatAction(step.action)}
          color={
            step.action.type === "shift"
              ? "primary"
              : step.action.type === "reduce"
                ? "success"
                : "warning"
          }
        />
      </Box>
    </Stack>
  );
}
