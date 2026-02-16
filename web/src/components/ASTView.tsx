import { SimpleTreeView, TreeItem } from "@mui/x-tree-view";
import { Typography } from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import type { ASTNodeOrToken } from "../api/types";

function renderNode(node: ASTNodeOrToken, id: string): React.ReactNode {
  if (node.type === "token") {
    return (
      <TreeItem
        key={id}
        itemId={id}
        label={
          <span style={{ fontFamily: "monospace" }}>
            <strong>{node.token}</strong>: "{node.lexeme}"
          </span>
        }
      />
    );
  }
  return (
    <TreeItem
      key={id}
      itemId={id}
      label={
        <span style={{ fontFamily: "monospace", fontWeight: "bold" }}>
          {node.symbol}
        </span>
      }
    >
      {node.children.map((child, i) => renderNode(child, `${id}-${i}`))}
    </TreeItem>
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
        {error
          ? `Parse error: ${error}`
          : 'Click "Parse" to see the AST.'}
      </Typography>
    );
  }

  return (
    <SimpleTreeView defaultExpandedItems={["root"]}>
      {renderNode(ast, "root")}
    </SimpleTreeView>
  );
}
