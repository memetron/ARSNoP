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

  if (!parseResult?.ast) {
    return (
      <Typography color="text.secondary">
        {parseResult?.error
          ? `Parse error: ${parseResult.error}`
          : 'Click "Parse" to see the AST.'}
      </Typography>
    );
  }

  return (
    <SimpleTreeView defaultExpandedItems={["root"]}>
      {renderNode(parseResult.ast, "root")}
    </SimpleTreeView>
  );
}
