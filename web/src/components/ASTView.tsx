import { Typography } from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import type { ASTNodeOrToken } from "../api/types";

function renderNode(node: ASTNodeOrToken, id: string): React.ReactNode {
  if (node.type === "token") {
    return (
      <div key={id} style={{ paddingLeft: 16, fontFamily: "monospace", lineHeight: "1.8em" }}>
        <strong>{node.token}</strong>: "{node.lexeme}"
      </div>
    );
  }
  return (
    <details key={id} open={id === "root"} style={{ paddingLeft: 16 }}>
      <summary style={{ fontFamily: "monospace", fontWeight: "bold", cursor: "pointer", lineHeight: "1.8em" }}>
        {node.symbol}
      </summary>
      {node.children.map((child, i) => renderNode(child, `${id}-${i}`))}
    </details>
  );
}

export default function ASTView() {
  const parseResult = useAppStore((s) => s.parseResult);
  const earleyResult = useAppStore((s) => s.earleyResult);

  const ast = parseResult?.ast ?? earleyResult?.ast ?? null;
  const error = parseResult?.error ?? earleyResult?.error;

  if (!ast) {
    return (
      <Typography color="text.secondary">
        {error ? `Parse error: ${error}` : 'Click "Parse" to see the AST.'}
      </Typography>
    );
  }

  return <div style={{ paddingLeft: 4 }}>{renderNode(ast, "root")}</div>;
}
