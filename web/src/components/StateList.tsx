import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useAppStore } from "../store/useAppStore";
import { formatItem } from "../utils/formatItem";

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
