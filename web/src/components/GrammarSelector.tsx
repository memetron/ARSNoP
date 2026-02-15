import { useEffect } from "react";
import { FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import { useAppStore } from "../store/useAppStore";

export default function GrammarSelector() {
  const bundledList = useAppStore((s) => s.bundledList);
  const selectedBundled = useAppStore((s) => s.selectedBundled);
  const loadBundledList = useAppStore((s) => s.loadBundledList);
  const loadBundledGrammar = useAppStore((s) => s.loadBundledGrammar);

  useEffect(() => {
    loadBundledList();
  }, [loadBundledList]);

  return (
    <FormControl fullWidth size="small">
      <InputLabel>Bundled Grammar</InputLabel>
      <Select
        value={selectedBundled}
        label="Bundled Grammar"
        onChange={(e) => loadBundledGrammar(e.target.value)}
      >
        <MenuItem value="">
          <em>Custom</em>
        </MenuItem>
        {bundledList.map((name) => (
          <MenuItem key={name} value={name}>
            {name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
