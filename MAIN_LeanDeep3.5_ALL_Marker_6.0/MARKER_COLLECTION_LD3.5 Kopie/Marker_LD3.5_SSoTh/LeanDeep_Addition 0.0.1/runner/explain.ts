import type { MarkerHit, ExplainabilityPayload } from "./types";

export async function explain(
  hits: MarkerHit[]
): Promise<ExplainabilityPayload> {
  const payload: ExplainabilityPayload = {};
  for (const h of hits) {
    payload[h.id] = { rules: [], offsets: [], confidence: 1.0 };
  }
  return payload;
}
