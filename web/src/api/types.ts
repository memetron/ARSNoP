export interface Production {
  lhs: string;
  rhs: string[];
}

export interface Item {
  production: Production;
  dot: number;
  lookahead: string[];
}

export interface State {
  index: number;
  items: Item[];
}

export interface ShiftAction {
  type: "shift";
  state: number;
}

export interface ReduceAction {
  type: "reduce";
  production: Production;
}

export interface AcceptAction {
  type: "accept";
}

export type Action = ShiftAction | ReduceAction | AcceptAction;

export type ActionTable = Record<string, Record<string, Action>>;
export type GotoTable = Record<string, Record<string, number>>;

export interface GrammarAnalysis {
  terminals: string[];
  nonTerminals: string[];
  productions: Production[];
  firstSets: Record<string, string[]>;
  followSets: Record<string, string[]>;
}

export interface TablesResult {
  states: State[];
  actionTable: ActionTable;
  gotoTable: GotoTable;
}

export interface TokenInfo {
  token: string;
  lexeme: string;
}

export interface TraceStep {
  step: number;
  stack: number[];
  inputBuffer: TokenInfo[];
  action: Action;
}

export interface ASTNode {
  type: "node";
  symbol: string;
  children: ASTNodeOrToken[];
}

export interface ASTToken {
  type: "token";
  token: string;
  lexeme: string;
}

export type ASTNodeOrToken = ASTNode | ASTToken;

export interface ParseResult {
  tokens: TokenInfo[];
  trace: TraceStep[];
  ast: ASTNodeOrToken | null;
  error?: string;
}

export type ParserVariant = "lr0" | "slr" | "lr1" | "lalr" | "lalr_brute_force";
