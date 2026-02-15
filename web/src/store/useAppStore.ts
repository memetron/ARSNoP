import { create } from "zustand";
import type {
  GrammarAnalysis,
  TablesResult,
  ParseResult,
  ParserVariant,
} from "../api/types";
import {
  fetchBundledList,
  fetchBundledGrammar,
  analyzeGrammar,
  generateTables,
  executeParse,
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

  // UI
  currentTraceStep: number;
  activeTab: number;
  loading: boolean;
  error: string | null;

  // Actions
  setGrammarText: (text: string) => void;
  setParserVariant: (variant: ParserVariant) => void;
  setInputText: (text: string) => void;
  setCurrentTraceStep: (step: number) => void;
  setActiveTab: (tab: number) => void;

  loadBundledList: () => Promise<void>;
  loadBundledGrammar: (name: string) => Promise<void>;
  doAnalyze: () => Promise<void>;
  doGenerateTables: () => Promise<void>;
  doParse: () => Promise<void>;
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
  currentTraceStep: 0,
  activeTab: 0,
  loading: false,
  error: null,

  setGrammarText: (text) => set({ grammarText: text }),
  setParserVariant: (variant) => set({ parserVariant: variant }),
  setInputText: (text) => set({ inputText: text }),
  setCurrentTraceStep: (step) => set({ currentTraceStep: step }),
  setActiveTab: (tab) => set({ activeTab: tab }),

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
        loading: false,
      });
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false });
    }
  },

  doAnalyze: async () => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const analysis = await analyzeGrammar(grammarText);
      set({ grammarAnalysis: analysis, activeTab: 0, loading: false });
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },

  doGenerateTables: async () => {
    const { grammarText, parserVariant } = get();
    try {
      set({ loading: true, error: null });
      const tables = await generateTables(grammarText, parserVariant);
      set({ tablesResult: tables, activeTab: 1, loading: false });
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },

  doParse: async () => {
    const { grammarText, parserVariant, inputText } = get();
    try {
      set({ loading: true, error: null });
      const result = await executeParse(grammarText, parserVariant, inputText);
      set({
        parseResult: result,
        currentTraceStep: 0,
        activeTab: 3,
        loading: false,
      });
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ?? (e instanceof Error ? e.message : String(e));
      set({ error: msg, loading: false });
    }
  },
}));
