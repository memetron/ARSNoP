import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useAppStore } from "../store/useAppStore";
import type { Item } from "../api/types";

function formatItem(item: Item): string {
  const rhs = [...item.production.rhs];
  rhs.splice(item.dot, 0, "\u2022"); // dot character
  const base = `${item.production.lhs} \u2192 ${rhs.join(" ")}`;
  if (item.lookahead.length > 0) {
    return `${base}  {${item.lookahead.join(", ")}}`;
  }
  return base;
}

export default function StateList() {
  const tablesResult = useAppStore((s) => s.tablesResult);

  if (!tablesResult) {
    return (
      <Typography color="text.secondary">
        Click "Generate Tables" to see states.
      </Typography>
    );
  }

  return (
    <Box>
      {tablesResult.states.map((state) => (
        <Accordion key={state.index} disableGutters>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">
              State {state.index}{" "}
              <Typography component="span" color="text.secondary" variant="body2">
                ({state.items.length} items)
              </Typography>
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {state.items.map((item, i) => (
              <Typography
                key={i}
                sx={{ fontFamily: "monospace", fontSize: "0.85rem" }}
              >
                {formatItem(item)}
              </Typography>
            ))}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
