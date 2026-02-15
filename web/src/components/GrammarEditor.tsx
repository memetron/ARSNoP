import CodeMirror from "@uiw/react-codemirror";
import { useAppStore } from "../store/useAppStore";

export default function GrammarEditor() {
  const grammarText = useAppStore((s) => s.grammarText);
  const setGrammarText = useAppStore((s) => s.setGrammarText);

  return (
    <CodeMirror
      value={grammarText}
      height="300px"
      onChange={(value) => setGrammarText(value)}
      basicSetup={{ lineNumbers: true, foldGutter: false }}
    />
  );
}
