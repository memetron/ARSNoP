import { useMemo } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Alert,
  LinearProgress,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Tabs,
  Tab,
} from "@mui/material";
import { Routes, Route, Navigate, useLocation, NavLink } from "react-router-dom";
import { useAppStore } from "./store/useAppStore";
import GrammarPage from "./pages/GrammarPage";
import GrammarInfoPage from "./pages/GrammarInfoPage";
import StatesPage from "./pages/StatesPage";
import TablesPage from "./pages/TablesPage";
import TracePage from "./pages/TracePage";
import ASTPage from "./pages/ASTPage";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1565c0" },
    secondary: { main: "#7b1fa2" },
  },
});

const NAV_ITEMS = [
  { label: "Grammar", path: "/grammar" },
  { label: "Grammar Info", path: "/grammar-info" },
  { label: "States", path: "/states" },
  { label: "Tables", path: "/tables" },
  { label: "Parse Trace", path: "/trace" },
  { label: "AST", path: "/ast" },
] as const;

export default function App() {
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);
  const location = useLocation();

  const activeTab = useMemo(() => {
    const idx = NAV_ITEMS.findIndex((item) => location.pathname === item.path);
    return idx >= 0 ? idx : 0;
  }, [location.pathname]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ fontWeight: "bold", mr: 2 }}>
            ARSNoP Demo
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8, mr: 4 }}>
            Interactive LR Parser Visualizer
          </Typography>
          <Tabs
            value={activeTab}
            textColor="inherit"
            indicatorColor="secondary"
            sx={{ ml: "auto" }}
          >
            {NAV_ITEMS.map((item) => (
              <Tab
                key={item.path}
                label={item.label}
                component={NavLink}
                to={item.path}
                sx={{ color: "inherit", opacity: 0.85, "&.active": { opacity: 1 } }}
              />
            ))}
          </Tabs>
        </Toolbar>
        {loading && <LinearProgress />}
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => useAppStore.setState({ error: null })}>
            {error}
          </Alert>
        )}
        <Routes>
          <Route path="/grammar" element={<GrammarPage />} />
          <Route path="/grammar-info" element={<GrammarInfoPage />} />
          <Route path="/states" element={<StatesPage />} />
          <Route path="/tables" element={<TablesPage />} />
          <Route path="/trace" element={<TracePage />} />
          <Route path="/ast" element={<ASTPage />} />
          <Route path="*" element={<Navigate to="/grammar" replace />} />
        </Routes>
      </Container>
    </ThemeProvider>
  );
}
