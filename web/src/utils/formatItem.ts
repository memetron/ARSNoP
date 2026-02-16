import type { Item } from "../api/types";

export function formatItem(item: Item): string {
  const rhs = [...item.production.rhs];
  rhs.splice(item.dot, 0, "\u2022"); // dot character
  const base = `${item.production.lhs} \u2192 ${rhs.join(" ")}`;
  if (item.lookahead.length > 0) {
    return `${base}  {${item.lookahead.join(", ")}}`;
  }
  return base;
}
