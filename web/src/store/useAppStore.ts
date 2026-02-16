import { create } from "zustand";
import type {
  GrammarAnalysis,
  TablesResult,
  ParseResult,
  ParserVariant,
  EarleyParseResult,
} from "../api/types";
import {
  fetchBundledList,
  fetchBundledGrammar,
  analyzeGrammar,
  generateTables,
  executeParse,
  executeEarleyParse,
} from "../api/client";

interface AppState {
  // Grammar
  grammarText: string;
  bundledList: string[];
  selectedBundled: string;
  grammarAnalysis: GrammarAnalysis | null;

  // Parser
  parserVariant: ParserVariant;
  tablesResult: TablesResult | null;

  // Parse execution
  inputText: string;
  parseResult: ParseResult | null;
  earleyResult: EarleyParseResult | null;

  // UI
  currentTraceStep: number;
  currentChartColumn: number;
  loading: boolean;
  error: string | null;

  // Actions
  setGrammarText: (text: string) => void;
  setParserVariant: (variant: ParserVariant) => void;
  setInputText: (text: string) => void;
  setCurrentTraceStep: (step: number) => void;
  setCurrentChartColumn: (col: number) => void;

  loadBundledList: () => Promise<void>;
  loadBundledGrammar: (name: string) => Promise<void>;
  doAnalyze: (navigate?: (path: string) => void) => Promise<void>;
  doGenerateTables: (navigate?: (path: string) => void) => Promise<void>;
  doParse: (navigate?: (path: string) => void) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  grammarText: "",
  bundledList: [],
  selectedBundled: "",
  grammarAnalysis: null,
  parserVariant: "slr",
  tablesResult: null,
  inputText: "",
  parseResult: null,
  earleyResult: null,
  currentTraceStep: 0,
  currentChartColumn: 0,
  loading: false,
  error: null,

  setGrammarText: (text) => set({ grammarText: text }),
  setParserVariant: (variant) => set({ parserVariant: variant }),
  setInputText: (text) => set({ inputText: text }),
  setCurrentTraceStep: (step) => set({ currentTraceStep: step }),
  setCurrentChartColumn: (col) => set({ currentChartColumn: col }),

  loadBundledList: async () => {
    try {
      const list = await fetchBundledList();
      set({ bundledList: list });
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e) });
    }
  },

  loadBundledGrammar: async (name) => {
    try {
      set({ loading: true, error: null, selectedBundled: name });
      const result = await fetchBundledGrammar(name);
      set({
        grammarText: result.text,
        grammarAnalysis: null,
        tablesResult: null,
        parseResult: null,
        earleyResult: null,
        loading: false,
      });
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false });
    }
  },

  doAnalyze: async (navigate) => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const analysis = await analyzeGrammar(grammarText);
      set({ grammarAnalysis: analysis, loading: false });
      navigate?.("/grammar-info");
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },

  doGenerateTables: async (navigate) => {
    const { grammarText, parserVariant } = get();
    try {
      set({ loading: true, error: null });
      const tables = await generateTables(grammarText, parserVariant);
      set({ tablesResult: tables, loading: false });
      navigate?.("/states");
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },

  doParse: async (navigate) => {
    const { grammarText, parserVariant, inputText } = get();
    try {
      set({ loading: true, error: null });
      if (parserVariant === "earley") {
        const result = await executeEarleyParse(grammarText, inputText);
        set({
          earleyResult: result,
          parseResult: null,
          currentChartColumn: 0,
          loading: false,
        });
        navigate?.("/chart");
      } else {
        const result = await executeParse(grammarText, parserVariant, inputText);
        set({
          parseResult: result,
          earleyResult: null,
          currentTraceStep: 0,
          loading: false,
        });
        navigate?.("/trace");
      }
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },
}));
