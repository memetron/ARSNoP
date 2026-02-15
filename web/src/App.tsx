import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Alert,
  LinearProgress,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from "@mui/material";
import { useAppStore } from "./store/useAppStore";
import GrammarPanel from "./components/GrammarPanel";
import ResultsPanel from "./components/ResultsPanel";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1565c0" },
    secondary: { main: "#7b1fa2" },
  },
});

export default function App() {
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            ARSNoP Demo
          </Typography>
          <Typography variant="body2" sx={{ ml: 2, opacity: 0.8 }}>
            Interactive LR Parser Visualizer
          </Typography>
        </Toolbar>
        {loading && <LinearProgress />}
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => useAppStore.setState({ error: null })}>
            {error}
          </Alert>
        )}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 2 }} variant="outlined">
              <GrammarPanel />
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 8 }}>
            <Paper sx={{ p: 2 }} variant="outlined">
              <ResultsPanel />
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}
