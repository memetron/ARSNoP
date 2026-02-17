import { useMemo, useState, useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  MarkerType,
  useNodesState,
  useEdgesState,
  BaseEdge,
  EdgeLabelRenderer,
  getStraightPath,
  type NodeProps,
  type EdgeProps,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import dagre from "@dagrejs/dagre";
import { useAppStore } from "../store/useAppStore";
import { formatItem } from "../utils/formatItem";
import type { State, Item } from "../api/types";

const MAX_VISIBLE_ITEMS = 6;
const NODE_WIDTH = 220;
const ITEM_LINE_HEIGHT = 18;
const NODE_HEADER_HEIGHT = 32;
const NODE_PADDING = 16;

function estimateNodeHeight(itemCount: number): number {
  const visibleItems = Math.min(itemCount, MAX_VISIBLE_ITEMS);
  const truncationLine = itemCount > MAX_VISIBLE_ITEMS ? ITEM_LINE_HEIGHT : 0;
  return NODE_HEADER_HEIGHT + NODE_PADDING + visibleItems * ITEM_LINE_HEIGHT + truncationLine;
}

interface StateNodeData extends Record<string, unknown> {
  state: State;
  onSelect: (state: State) => void;
}

function StateNode({ data }: NodeProps<Node<StateNodeData>>) {
  const { state, onSelect } = data;
  const visibleItems = state.items.slice(0, MAX_VISIBLE_ITEMS);
  const remaining = state.items.length - MAX_VISIBLE_ITEMS;

  return (
    <Box
      onClick={() => onSelect(state)}
      sx={{
        cursor: "pointer",
        border: "1px solid #90caf9",
        borderRadius: 1,
        bgcolor: "#fff",
        width: NODE_WIDTH,
        overflow: "hidden",
      }}
    >
      <Handle id="left" type="target" position={Position.Left} style={{ background: "#555" }} />
      <Handle id="top-source" type="source" position={Position.Top} style={{ background: "#555" }} />
      <Handle id="top-target" type="target" position={Position.Top} style={{ background: "#555" }} />
      <Box sx={{ bgcolor: "#1565c0", color: "#fff", px: 1, py: 0.5 }}>
        <Typography variant="caption" sx={{ fontWeight: "bold" }}>
          State {state.index}
        </Typography>
      </Box>
      <Box sx={{ px: 1, py: 0.5 }}>
        {visibleItems.map((item: Item, i: number) => (
          <Typography
            key={i}
            sx={{ fontFamily: "monospace", fontSize: "0.7rem", lineHeight: `${ITEM_LINE_HEIGHT}px`, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
          >
            {formatItem(item)}
          </Typography>
        ))}
        {remaining > 0 && (
          <Typography sx={{ fontSize: "0.7rem", color: "text.secondary", fontStyle: "italic", lineHeight: `${ITEM_LINE_HEIGHT}px` }}>
            ... and {remaining} more
          </Typography>
        )}
      </Box>
      <Handle id="right" type="source" position={Position.Right} style={{ background: "#555" }} />
    </Box>
  );
}

function LabeledEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  label,
  style,
  markerEnd,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} markerEnd={markerEnd} />
      {label && (
        <EdgeLabelRenderer>
          <Box
            sx={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
              bgcolor: "white",
              px: 0.5,
              borderRadius: 0.5,
              fontSize: "0.7rem",
              fontFamily: "monospace",
              border: "1px solid #ccc",
            }}
            className="nodrag nopan"
          >
            {label}
          </Box>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

function SelfLoopEdge({
  id,
  sourceX,
  sourceY,
  label,
  style,
  markerEnd,
}: EdgeProps) {
  const spread = 20;
  const liftHeight = 60;
  const edgePath = `M ${sourceX - spread},${sourceY} C ${sourceX - spread},${sourceY - liftHeight} ${sourceX + spread},${sourceY - liftHeight} ${sourceX + spread},${sourceY}`;
  const labelX = sourceX;
  const labelY = sourceY - liftHeight;

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} markerEnd={markerEnd} />
      {label && (
        <EdgeLabelRenderer>
          <Box
            sx={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
              bgcolor: "white",
              px: 0.5,
              borderRadius: 0.5,
              fontSize: "0.7rem",
              fontFamily: "monospace",
              border: "1px solid #ccc",
            }}
            className="nodrag nopan"
          >
            {label}
          </Box>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

const nodeTypes = { stateNode: StateNode };
const edgeTypes = { labeled: LabeledEdge, selfLoop: SelfLoopEdge };

export default function StateGraph() {
  const tablesResult = useAppStore((s) => s.tablesResult);
  const [selectedState, setSelectedState] = useState<State | null>(null);

  const handleSelect = useCallback((state: State) => {
    setSelectedState(state);
  }, []);

  const { layoutNodes, layoutEdges } = useMemo(() => {
    if (!tablesResult) return { layoutNodes: [], layoutEdges: [] };

    const { states, actionTable, gotoTable } = tablesResult;

    // Build edges from action and goto tables
    const edgeMap = new Map<string, { source: string; target: string; label: string; type: "shift" | "goto" }>();

    // Shift edges from actionTable
    for (const [stateIdx, actions] of Object.entries(actionTable)) {
      for (const [symbol, action] of Object.entries(actions)) {
        if (action.type === "shift") {
          const key = `${stateIdx}-${action.state}-${symbol}`;
          if (!edgeMap.has(key)) {
            edgeMap.set(key, {
              source: stateIdx,
              target: String(action.state),
              label: symbol,
              type: "shift",
            });
          }
        }
      }
    }

    // Goto edges from gotoTable
    for (const [stateIdx, gotos] of Object.entries(gotoTable)) {
      for (const [symbol, targetState] of Object.entries(gotos)) {
        const key = `${stateIdx}-${targetState}-${symbol}`;
        if (!edgeMap.has(key)) {
          edgeMap.set(key, {
            source: stateIdx,
            target: String(targetState),
            label: symbol,
            type: "goto",
          });
        }
      }
    }

    // Layout with dagre
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: "LR", nodesep: 50, ranksep: 100 });
    g.setDefaultEdgeLabel(() => ({}));

    for (const state of states) {
      const h = estimateNodeHeight(state.items.length);
      g.setNode(String(state.index), { width: NODE_WIDTH, height: h });
    }

    for (const edge of edgeMap.values()) {
      g.setEdge(edge.source, edge.target);
    }

    dagre.layout(g);

    const nodes: Node<StateNodeData>[] = states.map((state) => {
      const pos = g.node(String(state.index));
      return {
        id: String(state.index),
        type: "stateNode",
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - pos.height / 2 },
        data: { state, onSelect: handleSelect },
      };
    });

    const edges: Edge[] = Array.from(edgeMap.entries()).map(([key, e]) => {
      const isSelfLoop = e.source === e.target;
      return {
        id: key,
        source: e.source,
        target: e.target,
        type: isSelfLoop ? "selfLoop" : "labeled",
        label: e.label,
        style: { stroke: e.type === "shift" ? "#1565c0" : "#7b1fa2", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: e.type === "shift" ? "#1565c0" : "#7b1fa2" },
        sourceHandle: isSelfLoop ? "top-source" : "right",
        targetHandle: isSelfLoop ? "top-target" : "left",
        ...(isSelfLoop && { zIndex: 1 }),
      };
    });

    return { layoutNodes: nodes, layoutEdges: edges };
  }, [tablesResult, handleSelect]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutEdges);

  // Sync when layout data changes (e.g. new tables generated)
  useEffect(() => {
    setNodes(layoutNodes);
    setEdges(layoutEdges);
  }, [layoutNodes, layoutEdges, setNodes, setEdges]);

  if (!tablesResult) {
    return (
      <Typography color="text.secondary">
        Click "Generate Tables" to see the state graph.
      </Typography>
    );
  }

  return (
    <>
      <Box sx={{ height: "70vh", border: "1px solid #e0e0e0", borderRadius: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </Box>

      <Dialog
        open={selectedState !== null}
        onClose={() => setSelectedState(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedState && (
          <>
            <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              State {selectedState.index}
              <IconButton onClick={() => setSelectedState(null)} size="small">
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers>
              {selectedState.items.map((item: Item, i: number) => (
                <Typography
                  key={i}
                  sx={{ fontFamily: "monospace", fontSize: "0.85rem", lineHeight: 1.8 }}
                >
                  {formatItem(item)}
                </Typography>
              ))}
            </DialogContent>
          </>
        )}
      </Dialog>
    </>
  );
}
