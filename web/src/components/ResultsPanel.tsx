import { Box, Tab, Tabs, Stack } from "@mui/material";
import { useAppStore } from "../store/useAppStore";
import GrammarInfo from "./GrammarInfo";
import StateList from "./StateList";
import ActionTableView from "./ActionTableView";
import GotoTableView from "./GotoTableView";
import TraceDebugger from "./TraceDebugger";
import TraceTable from "./TraceTable";
import ASTView from "./ASTView";

export default function ResultsPanel() {
  const activeTab = useAppStore((s) => s.activeTab);
  const setActiveTab = useAppStore((s) => s.setActiveTab);

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={(_, val) => setActiveTab(val)}
        variant="scrollable"
        scrollButtons="auto"
      >
        <Tab label="Grammar Info" />
        <Tab label="States" />
        <Tab label="Tables" />
        <Tab label="Parse Trace" />
        <Tab label="AST" />
      </Tabs>
      <Box sx={{ pt: 2 }}>
        {activeTab === 0 && <GrammarInfo />}
        {activeTab === 1 && <StateList />}
        {activeTab === 2 && (
          <Stack spacing={3}>
            <ActionTableView />
            <GotoTableView />
          </Stack>
        )}
        {activeTab === 3 && (
          <Stack spacing={3}>
            <TraceDebugger />
            <TraceTable />
          </Stack>
        )}
        {activeTab === 4 && <ASTView />}
      </Box>
    </Box>
  );
}
