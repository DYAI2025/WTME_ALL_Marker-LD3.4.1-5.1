import type { MarkerHit, Span } from "./types";

export async function detect_ato(text: string): Promise<MarkerHit[]> {
  // Placeholder: engine wiring happens in compose/aggregate
  const hits: MarkerHit[] = [];
  // Real impl would iterate registry of ATO patterns
  return hits;
}
