export type ReviewState =
  | "system-supported"
  | "pending"
  | "approved"
  | "rejected";

export type ConfidenceLevel =
  | "high"
  | "moderate"
  | "low";

export type EvidenceItem = {
  id: string;
  source: string;
  excerpt: string;
  relevance: number;
};

export type Finding = {
  id: string;
  claim: string;

  confidence: {
    level: ConfidenceLevel;
    label: string;
    basis: string;
  };

  surfacedBy: string;
  verifiedBy: string;

  evidence: EvidenceItem[];

  review: {
    state: ReviewState;
    note: string;
  };
};

export type AgentTraceStep = {
  id: string;
  agent: string;
  action: string;
};

export type EvaluationMetric = {
  id: string;
  label: string;
  value: number;
  method: string;
  measures: string[];
};

export type ResearchRun = {
  id: string;
  question: string;

  status:
    | "completed"
    | "partial"
    | "failed";

  sourceCount: number;
  agentCount: number;
  durationSeconds: number;

  findings: Finding[];

  agentTrace: AgentTraceStep[];

  evaluation: EvaluationMetric[];
};