import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import type { ParserVariant } from "../api/types";

const variants: { value: ParserVariant; label: string }[] = [
  { value: "earley", label: "Earley" },
  { value: "lr0", label: "LR(0)" },
  { value: "slr", label: "SLR(1)" },
  { value: "lr1", label: "LR(1)" },
  { value: "lalr", label: "LALR(1)" },
  { value: "lalr_brute_force", label: "LALR BF" },
];

export default function ParserSelector() {
  const parserVariant = useAppStore((s) => s.parserVariant);
  const setParserVariant = useAppStore((s) => s.setParserVariant);

  return (
    <ToggleButtonGroup
      value={parserVariant}
      exclusive
      onChange={(_, val) => val && setParserVariant(val as ParserVariant)}
      size="small"
      fullWidth
    >
      {variants.map((v) => (
        <ToggleButton key={v.value} value={v.value}>
          {v.label}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}
