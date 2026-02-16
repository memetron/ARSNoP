import { Button, Stack } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";

export default function ActionButtons() {
  const doAnalyze = useAppStore((s) => s.doAnalyze);
  const doGenerateTables = useAppStore((s) => s.doGenerateTables);
  const doParse = useAppStore((s) => s.doParse);
  const loading = useAppStore((s) => s.loading);
  const parserVariant = useAppStore((s) => s.parserVariant);
  const navigate = useNavigate();

  return (
    <Stack direction="row" spacing={1}>
      <Button
        variant="outlined"
        onClick={() => doAnalyze(navigate)}
        disabled={loading}
      >
        Analyze
      </Button>
      {parserVariant !== "earley" && (
        <Button
          variant="contained"
          onClick={() => doGenerateTables(navigate)}
          disabled={loading}
        >
          Generate Tables
        </Button>
      )}
      <Button
        variant="contained"
        color="secondary"
        onClick={() => doParse(navigate)}
        disabled={loading}
      >
        Parse
      </Button>
    </Stack>
  );
}
