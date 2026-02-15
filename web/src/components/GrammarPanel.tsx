import { Stack, TextField } from "@mui/material";
import GrammarSelector from "./GrammarSelector";
import GrammarEditor from "./GrammarEditor";
import ParserSelector from "./ParserSelector";
import ActionButtons from "./ActionButtons";
import { useAppStore } from "../store/useAppStore";

export default function GrammarPanel() {
  const inputText = useAppStore((s) => s.inputText);
  const setInputText = useAppStore((s) => s.setInputText);

  return (
    <Stack spacing={2}>
      <GrammarSelector />
      <GrammarEditor />
      <ParserSelector />
      <TextField
        label="Input to parse"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        size="small"
        fullWidth
      />
      <ActionButtons />
    </Stack>
  );
}
