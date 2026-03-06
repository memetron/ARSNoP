import { useMemo, useState, useRef, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Tooltip,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import FitScreenIcon from "@mui/icons-material/FitScreen";
import { useAppStore } from "../store/useAppStore";
import { formatItem } from "../utils/formatItem";
import type { State, Item } from "../api/types";

const MAX_VISIBLE_ITEMS = 6;
const NODE_WIDTH = 220;
const ITEM_LINE_HEIGHT = 18;
const NODE_HEADER_HEIGHT = 32;
const NODE_PADDING = 16;
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 2;
const ZOOM_STEP = 0.15;

function estimateNodeHeight(itemCount: number): number {
  const visibleItems = Math.min(itemCount, MAX_VISIBLE_ITEMS);
  const truncationLine = itemCount > MAX_VISIBLE_ITEMS ? ITEM_LINE_HEIGHT : 0;
  return NODE_HEADER_HEIGHT + NODE_PADDING + visibleItems * ITEM_LINE_HEIGHT + truncationLine;
}

interface GraphNode {
  id: string;
  cx: number;
  cy: number;
  width: number;
  height: number;
  state: State;
}

interface GraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  label: string;
  edgeType: "shift" | "goto";
  isSelfLoop: boolean;
}

interface ViewTransform {
  x: number;
  y: number;
  scale: number;
}

function computeGraphBounds(nodes: GraphNode[]) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    minX = Math.min(minX, n.cx - n.width / 2);
    minY = Math.min(minY, n.cy - n.height / 2);
    maxX = Math.max(maxX, n.cx + n.width / 2);
    maxY = Math.max(maxY, n.cy + n.height / 2);
  }
  return { minX, minY, maxX, maxY };
}

function fitViewTransform(
  nodes: GraphNode[],
  containerW: number,
  containerH: number,
): ViewTransform {
  const padding = 40;
  const { minX, minY, maxX, maxY } = computeGraphBounds(nodes);
  const graphW = maxX - minX;
  const graphH = maxY - minY;
  const rawScale = Math.min(
    (containerW - padding * 2) / graphW,
    (containerH - padding * 2) / graphH,
  );
  const scale = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, rawScale));
  const x = (containerW - graphW * scale) / 2 - minX * scale;
  const y = (containerH - graphH * scale) / 2 - minY * scale;
  return { x, y, scale };
}

const RANK_SEP = 140;
const NODE_SEP = 20;

/** BFS from state 0 to assign each node a rank (column index). */
function assignRanks(nodeIds: string[], edges: GraphEdge[]): Map<string, number> {
  const adj = new Map<string, string[]>(nodeIds.map((id) => [id, []]));
  for (const edge of edges) {
    if (!edge.isSelfLoop) adj.get(edge.sourceId)?.push(edge.targetId);
  }

  const rank = new Map<string, number>(nodeIds.map((id) => [id, -1]));
  rank.set("0", 0);
  const queue = ["0"];
  while (queue.length > 0) {
    const curr = queue.shift()!;
    for (const next of adj.get(curr) ?? []) {
      if (rank.get(next) === -1) {
        rank.set(next, rank.get(curr)! + 1);
        queue.push(next);
      }
    }
  }
  // Unreachable nodes fall back to rank 0
  for (const id of nodeIds) {
    if (rank.get(id) === -1) rank.set(id, 0);
  }
  return rank;
}

/** Compute (cx, cy) center positions for each node using a rank-based layout. */
function computePositions(
  nodeIds: string[],
  edges: GraphEdge[],
  nodeHeights: Map<string, number>,
): Map<string, { cx: number; cy: number }> {
  const rank = assignRanks(nodeIds, edges);

  const rankGroups = new Map<number, string[]>();
  for (const id of nodeIds) {
    const r = rank.get(id)!;
    if (!rankGroups.has(r)) rankGroups.set(r, []);
    rankGroups.get(r)!.push(id);
  }
  for (const group of rankGroups.values()) {
    group.sort((a, b) => +a - +b);
  }

  const positions = new Map<string, { cx: number; cy: number }>();
  for (const [r, group] of rankGroups) {
    const cx = r * (NODE_WIDTH + RANK_SEP) + NODE_WIDTH / 2;
    const totalH =
      group.reduce((sum, id) => sum + (nodeHeights.get(id) ?? 60), 0) +
      NODE_SEP * (group.length - 1);
    let y = -totalH / 2;
    for (const id of group) {
      const h = nodeHeights.get(id) ?? 60;
      positions.set(id, { cx, cy: y + h / 2 });
      y += h + NODE_SEP;
    }
  }
  return positions;
}

function buildLayout(tablesResult: NonNullable<ReturnType<typeof useAppStore>["tablesResult"]>) {
  const { states, actionTable, gotoTable } = tablesResult;

  const edgeMap = new Map<string, GraphEdge>();

  for (const [stateIdx, actions] of Object.entries(actionTable)) {
    for (const [symbol, action] of Object.entries(actions)) {
      if (action.type === "shift") {
        const key = `${stateIdx}-${action.state}-${symbol}`;
        if (!edgeMap.has(key)) {
          edgeMap.set(key, {
            id: key,
            sourceId: stateIdx,
            targetId: String(action.state),
            label: symbol,
            edgeType: "shift",
            isSelfLoop: stateIdx === String(action.state),
          });
        }
      }
    }
  }

  for (const [stateIdx, gotos] of Object.entries(gotoTable)) {
    for (const [symbol, targetState] of Object.entries(gotos)) {
      const key = `${stateIdx}-${targetState}-${symbol}`;
      if (!edgeMap.has(key)) {
        edgeMap.set(key, {
          id: key,
          sourceId: stateIdx,
          targetId: String(targetState),
          label: symbol,
          edgeType: "goto",
          isSelfLoop: stateIdx === String(targetState),
        });
      }
    }
  }

  const nodeIds = states.map((s) => String(s.index));
  const nodeHeights = new Map(states.map((s) => [String(s.index), estimateNodeHeight(s.items.length)]));
  const graphEdges = Array.from(edgeMap.values());
  const positions = computePositions(nodeIds, graphEdges, nodeHeights);

  const graphNodes: GraphNode[] = states.flatMap((state) => {
    const pos = positions.get(String(state.index));
    if (!pos) return [];
    return [{ id: String(state.index), cx: pos.cx, cy: pos.cy, width: NODE_WIDTH, height: nodeHeights.get(String(state.index))!, state }];
  });

  return { graphNodes, graphEdges };
}

export default function StateGraph() {
  const tablesResult = useAppStore((s) => s.tablesResult);
  const [selectedState, setSelectedState] = useState<State | null>(null);
  const [transform, setTransform] = useState<ViewTransform>({ x: 0, y: 0, scale: 1 });
  const svgRef = useRef<SVGSVGElement>(null);
  const isPanning = useRef(false);
  const hasDragged = useRef(false);
  const panOrigin = useRef({ x: 0, y: 0 });
  const transformSnapshot = useRef<ViewTransform>({ x: 0, y: 0, scale: 1 });
  const transformRef = useRef(transform);
  transformRef.current = transform;
  const [nodePositions, setNodePositions] = useState<Map<string, { cx: number; cy: number }>>(new Map());
  const nodePositionsRef = useRef(nodePositions);
  nodePositionsRef.current = nodePositions;
  const draggingNodeId = useRef<string | null>(null);
  const nodeDragStart = useRef({ mouseX: 0, mouseY: 0, cx: 0, cy: 0 });

  const { graphNodes, graphEdges } = useMemo(
    () => (tablesResult ? buildLayout(tablesResult) : { graphNodes: [], graphEdges: [] }),
    [tablesResult],
  );

  const nodeMap = useMemo(() => new Map(graphNodes.map((n) => [n.id, n])), [graphNodes]);

  // Reset positions when the layout changes (new parse result)
  useEffect(() => {
    setNodePositions(new Map(graphNodes.map((n) => [n.id, { cx: n.cx, cy: n.cy }])));
  }, [graphNodes]);

  const doFitView = useCallback(() => {
    if (!svgRef.current || graphNodes.length === 0) return;
    const { width, height } = svgRef.current.getBoundingClientRect();
    if (width === 0 || height === 0) return;
    const currentNodes = graphNodes.map((n) => ({
      ...n,
      cx: nodePositionsRef.current.get(n.id)?.cx ?? n.cx,
      cy: nodePositionsRef.current.get(n.id)?.cy ?? n.cy,
    }));
    setTransform(fitViewTransform(currentNodes, width, height));
  }, [graphNodes]);

  useEffect(() => {
    const id = requestAnimationFrame(doFitView);
    return () => cancelAnimationFrame(id);
  }, [doFitView]);

  // Non-passive wheel listener so we can preventDefault
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      setTransform((t) => {
        const newScale = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, t.scale * factor));
        const rect = svg.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const x = mx - (mx - t.x) * (newScale / t.scale);
        const y = my - (my - t.y) * (newScale / t.scale);
        return { x, y, scale: newScale };
      });
    };
    svg.addEventListener("wheel", onWheel, { passive: false });
    return () => svg.removeEventListener("wheel", onWheel);
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (e.button !== 0) return;
    isPanning.current = true;
    hasDragged.current = false;
    panOrigin.current = { x: e.clientX, y: e.clientY };
    transformSnapshot.current = { ...transformRef.current };
    if (svgRef.current) svgRef.current.style.cursor = "grabbing";
  }, []);

  const handleNodeMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    const pos = nodePositionsRef.current.get(nodeId);
    if (!pos) return;
    draggingNodeId.current = nodeId;
    hasDragged.current = false;
    nodeDragStart.current = { mouseX: e.clientX, mouseY: e.clientY, cx: pos.cx, cy: pos.cy };
    if (svgRef.current) svgRef.current.style.cursor = "grabbing";
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (draggingNodeId.current !== null) {
      const dx = e.clientX - nodeDragStart.current.mouseX;
      const dy = e.clientY - nodeDragStart.current.mouseY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) hasDragged.current = true;
      const scale = transformRef.current.scale;
      const id = draggingNodeId.current;
      setNodePositions((prev) => {
        const next = new Map(prev);
        next.set(id, { cx: nodeDragStart.current.cx + dx / scale, cy: nodeDragStart.current.cy + dy / scale });
        return next;
      });
      return;
    }
    if (!isPanning.current) return;
    const dx = e.clientX - panOrigin.current.x;
    const dy = e.clientY - panOrigin.current.y;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) hasDragged.current = true;
    setTransform({ ...transformSnapshot.current, x: transformSnapshot.current.x + dx, y: transformSnapshot.current.y + dy });
  }, []);

  const stopDragging = useCallback(() => {
    isPanning.current = false;
    draggingNodeId.current = null;
    if (svgRef.current) svgRef.current.style.cursor = "grab";
  }, []);

  const handleNodeClick = useCallback((state: State) => {
    if (hasDragged.current) return;
    setSelectedState(state);
  }, []);

  if (!tablesResult) {
    return (
      <Typography color="text.secondary">
        Click "Generate Tables" to see the state graph.
      </Typography>
    );
  }

  return (
    <>
      <Box sx={{ height: "70vh", border: "1px solid #e0e0e0", borderRadius: 1, position: "relative", overflow: "hidden" }}>
        <svg
          ref={svgRef}
          style={{ width: "100%", height: "100%", cursor: "grab", display: "block" }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={stopDragging}
          onMouseLeave={stopDragging}
        >
          <defs>
            <marker id="arrow-shift" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#1565c0" />
            </marker>
            <marker id="arrow-goto" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#7b1fa2" />
            </marker>
          </defs>
          <g transform={`translate(${transform.x},${transform.y}) scale(${transform.scale})`}>
            {graphEdges.map((edge) => {
              const srcMeta = nodeMap.get(edge.sourceId);
              const tgtMeta = nodeMap.get(edge.targetId);
              if (!srcMeta || !tgtMeta) return null;
              const srcPos = nodePositions.get(edge.sourceId) ?? { cx: srcMeta.cx, cy: srcMeta.cy };
              const tgtPos = nodePositions.get(edge.targetId) ?? { cx: tgtMeta.cx, cy: tgtMeta.cy };
              const color = edge.edgeType === "shift" ? "#1565c0" : "#7b1fa2";
              const markerId = `url(#arrow-${edge.edgeType})`;

              let pathD: string;
              let labelX: number;
              let labelY: number;

              if (edge.isSelfLoop) {
                const topY = srcPos.cy - srcMeta.height / 2;
                const spread = 20;
                const lift = 60;
                pathD = `M ${srcPos.cx - spread},${topY} C ${srcPos.cx - spread},${topY - lift} ${srcPos.cx + spread},${topY - lift} ${srcPos.cx + spread},${topY}`;
                labelX = srcPos.cx;
                labelY = topY - lift - 8;
              } else {
                const sx = srcPos.cx + srcMeta.width / 2;
                const sy = srcPos.cy;
                const tx = tgtPos.cx - tgtMeta.width / 2;
                const ty = tgtPos.cy;
                const cpx1 = sx + (tx - sx) * 0.4;
                const cpx2 = tx - (tx - sx) * 0.4;
                pathD = `M ${sx},${sy} C ${cpx1},${sy} ${cpx2},${ty} ${tx},${ty}`;
                labelX = (sx + tx) / 2;
                labelY = (sy + ty) / 2 - 8;
              }

              const labelW = Math.max(20, edge.label.length * 6.6 + 8);
              return (
                <g key={edge.id}>
                  <path d={pathD} fill="none" stroke={color} strokeWidth={2} markerEnd={markerId} />
                  <rect x={labelX - labelW / 2} y={labelY - 9} width={labelW} height={18} fill="white" stroke="#ccc" strokeWidth={1} rx={2} />
                  <text x={labelX} y={labelY} textAnchor="middle" dominantBaseline="middle" fontFamily="monospace" fontSize={11} fill={color}>
                    {edge.label}
                  </text>
                </g>
              );
            })}
            {graphNodes.map((node) => {
              const pos = nodePositions.get(node.id) ?? { cx: node.cx, cy: node.cy };
              const x = pos.cx - node.width / 2;
              const y = pos.cy - node.height / 2;
              const visibleItems = node.state.items.slice(0, MAX_VISIBLE_ITEMS);
              const remaining = node.state.items.length - MAX_VISIBLE_ITEMS;
              return (
                <foreignObject
                  key={node.id}
                  x={x}
                  y={y}
                  width={node.width}
                  height={node.height}
                  style={{ cursor: "grab", overflow: "visible" }}
                  onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
                  onClick={() => handleNodeClick(node.state)}
                >
                  <Box
                    sx={{
                      border: "1px solid #90caf9",
                      borderRadius: 1,
                      bgcolor: "#fff",
                      width: node.width,
                      height: node.height,
                      overflow: "hidden",
                      boxSizing: "border-box",
                    }}
                  >
                    <Box sx={{ bgcolor: "#1565c0", color: "#fff", px: 1, py: 0.5, height: NODE_HEADER_HEIGHT, display: "flex", alignItems: "center" }}>
                      <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                        State {node.state.index}
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
                  </Box>
                </foreignObject>
              );
            })}
          </g>
        </svg>
        <Box sx={{ position: "absolute", bottom: 16, right: 16, display: "flex", flexDirection: "column", gap: 0.5 }}>
          <Tooltip title="Zoom in" placement="left">
            <IconButton
              size="small"
              onClick={() => setTransform((t) => ({ ...t, scale: Math.min(MAX_ZOOM, t.scale + ZOOM_STEP) }))}
              sx={{ bgcolor: "white", border: "1px solid #e0e0e0", "&:hover": { bgcolor: "#f5f5f5" } }}
            >
              <ZoomInIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom out" placement="left">
            <IconButton
              size="small"
              onClick={() => setTransform((t) => ({ ...t, scale: Math.max(MIN_ZOOM, t.scale - ZOOM_STEP) }))}
              sx={{ bgcolor: "white", border: "1px solid #e0e0e0", "&:hover": { bgcolor: "#f5f5f5" } }}
            >
              <ZoomOutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Fit view" placement="left">
            <IconButton
              size="small"
              onClick={doFitView}
              sx={{ bgcolor: "white", border: "1px solid #e0e0e0", "&:hover": { bgcolor: "#f5f5f5" } }}
            >
              <FitScreenIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Dialog open={selectedState !== null} onClose={() => setSelectedState(null)} maxWidth="sm" fullWidth>
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
                <Typography key={i} sx={{ fontFamily: "monospace", fontSize: "0.85rem", lineHeight: 1.8 }}>
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
