import { Button, Stack } from "@mui/material";
import { useAppStore } from "../store/useAppStore";

export default function ActionButtons() {
  const doAnalyze = useAppStore((s) => s.doAnalyze);
  const doGenerateTables = useAppStore((s) => s.doGenerateTables);
  const doParse = useAppStore((s) => s.doParse);
  const loading = useAppStore((s) => s.loading);

  return (
    <Stack direction="row" spacing={1}>
      <Button
        variant="outlined"
        onClick={doAnalyze}
        disabled={loading}
      >
        Analyze
      </Button>
      <Button
        variant="contained"
        onClick={doGenerateTables}
        disabled={loading}
      >
        Generate Tables
      </Button>
      <Button
        variant="contained"
        color="secondary"
        onClick={doParse}
        disabled={loading}
      >
        Parse
      </Button>
    </Stack>
  );
}
