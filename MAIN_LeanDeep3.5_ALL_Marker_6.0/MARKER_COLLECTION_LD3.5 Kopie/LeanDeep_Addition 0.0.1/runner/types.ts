export type Span = { start: number; end: number };
export type MarkerHit = {
  id: string;
  level: "ATO" | "SEM" | "CLU" | "MEMA";
  score: number;
  ranges: Span[];
};
export type ExplainabilityPayload = Record<
  string,
  {
    rules: string[];
    features?: Record<string, any>;
    offsets: number[];
    confidence: number;
  }
>;
export type AnalyzeReq = {
  text: string;
  markerPaths: string[];
  options?: { useIntuition?: boolean };
};
