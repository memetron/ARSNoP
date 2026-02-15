import axios from "axios";
import type {
  GrammarAnalysis,
  TablesResult,
  ParseResult,
  ParserVariant,
} from "./types";

const api = axios.create({ baseURL: "/api" });

export async function fetchBundledList(): Promise<string[]> {
  const { data } = await api.get<string[]>("/grammar/bundled");
  return data;
}

export async function fetchBundledGrammar(
  name: string
): Promise<{ name: string; text: string }> {
  const { data } = await api.get<{ name: string; text: string }>(
    `/grammar/bundled/${name}`
  );
  return data;
}

export async function analyzeGrammar(
  grammar: string
): Promise<GrammarAnalysis> {
  const { data } = await api.post<GrammarAnalysis>("/grammar/analyze", {
    grammar,
  });
  return data;
}

export async function generateTables(
  grammar: string,
  variant: ParserVariant
): Promise<TablesResult> {
  const { data } = await api.post<TablesResult>("/parse/tables", {
    grammar,
    variant,
  });
  return data;
}

export async function executeParse(
  grammar: string,
  variant: ParserVariant,
  input: string
): Promise<ParseResult> {
  const { data } = await api.post<ParseResult>("/parse/execute", {
    grammar,
    variant,
    input,
  });
  return data;
}
