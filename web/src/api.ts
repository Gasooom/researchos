import type {
  AgentTraceStep,
  EvaluationMetric,
  Finding,
  ResearchRun,
  ReviewState,
} from "./types";

type ApiReviewStatus =
  | "not_required"
  | "pending"
  | "approved"
  | "rejected";

type ApiEvidence = {
  source: {
    title: string;
    url: string;
    publisher: string;
    retrieved_at: string;
  };
  excerpt: string;
  relevance: number;
};

type ApiClaim = {
  statement: string;
  evidence: ApiEvidence[];
  review_status: ApiReviewStatus;
};

type ApiResearchResult = {
  question: string;
  claims: ApiClaim[];
  sources: Array<{
    title: string;
    url: string;
    publisher: string;
    retrieved_at: string;
  }>;
  execution?: {
    status: "success" | "partial" | "failed";
    completed_tasks: number;
    failed_tasks: number;
    failures: Array<{
      task_objective: string;
      error_type: string;
      message: string;
    }>;
    evidence: unknown[];
  } | null;
};

type ApiExecution = {
  status: "success" | "partial" | "failed";
  completed_tasks: number;
  failed_tasks: number;
  failures: Array<{
    task_objective: string;
    error_type: string;
    message: string;
  }>;
  evidence: unknown[];
};

type ApiMultiAgentResult = {
  evidence: ApiEvidence[];
  analysis: {
    summary: string;
    key_points: string[];
    confidence: number;
  };
  synthesis: {
    answer: string;
    supporting_points: string[];
    confidence: number;
  };
};

type ApiEvaluationMetric = {
  name: string;
  value: number;
  description: string;
};

type ApiEvaluation = {
  metrics: ApiEvaluationMetric[];
  overall_score: number;
};

type ApiObservation = {
  duration_seconds: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  status: "success" | "partial" | "failed";
};

type WorkspaceResponse = {
  result: ApiResearchResult;
  execution: ApiExecution;
  agents: ApiMultiAgentResult[];
  evaluation: ApiEvaluation;
  observation: ApiObservation | null;
};

function mapExecutionStatus(
  status: ApiExecution["status"],
): ResearchRun["status"] {
  switch (status) {
    case "success":
      return "completed";

    case "partial":
      return "partial";

    case "failed":
      return "failed";
  }
}

function mapReviewState(
  status: ApiReviewStatus,
): ReviewState {
  switch (status) {
    case "not_required":
      return "system-supported";

    case "pending":
      return "pending";

    case "approved":
      return "approved";

    case "rejected":
      return "rejected";
  }
}

function buildReviewNote(
  status: ApiReviewStatus,
): string {
  switch (status) {
    case "not_required":
      return "The claim passed the system review policy and does not currently require human review.";

    case "pending":
      return "The system flagged this claim for human review because the available evidence does not fully support the current wording.";

    case "approved":
      return "This claim has been approved by the human review workflow.";

    case "rejected":
      return "This claim was rejected by the human review workflow and requires revision.";
  }
}

function mapEvaluation(
  evaluation: ApiEvaluation,
): EvaluationMetric[] {
  return evaluation.metrics.map((metric) => ({
    id: metric.name,
    label: metric.name
      .replaceAll("_", " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase(),
      ),
    value: metric.value,
    method: metric.description,
    measures: [],
  }));
}

function mapAgentTrace(
  hasMultiAgentResults: boolean,
): AgentTraceStep[] {
  if (!hasMultiAgentResults) {
    return [
      {
        id: "planner",
        agent: "Planner",
        action: "Research plan created",
      },
      {
        id: "research",
        agent: "Research pipeline",
        action: "Evidence retrieved and assembled",
      },
      {
        id: "verification",
        agent: "Claim verification",
        action: "Claims checked against evidence",
      },
      {
        id: "synthesis",
        agent: "Synthesis",
        action: "Research result assembled",
      },
    ];
  }

  return [
    {
      id: "planner",
      agent: "Planner",
      action: "Research plan created",
    },
    {
      id: "retrieval",
      agent: "Retrieval Agent",
      action: "Sources and evidence retrieved",
    },
    {
      id: "analysis",
      agent: "Analysis Agent",
      action: "Evidence analyzed",
    },
    {
      id: "synthesis",
      agent: "Synthesis Agent",
      action: "Findings synthesized",
    },
    {
      id: "verification",
      agent: "Claim verification",
      action: "Claims checked against evidence",
    },
  ];
}

function mapConfidence(
  claim: ApiClaim,
) {
  const independentSourceCount = new Set(
    claim.evidence.map(
      (evidence) => evidence.source.url,
    ),
  ).size;

  const averageRelevance =
    claim.evidence.length === 0
      ? 0
      : claim.evidence.reduce(
          (sum, evidence) =>
            sum + evidence.relevance,
          0,
        ) / claim.evidence.length;

  if (
    averageRelevance >= 0.8 &&
    independentSourceCount >= 2
  ) {
    return {
      level: "high" as const,
      label: "High confidence",
      basis: `corroborated by ${independentSourceCount} independent sources`,
    };
  }

  if (averageRelevance >= 0.7) {
    return {
      level: "moderate" as const,
      label: "Moderate confidence",
      basis:
        independentSourceCount >= 2
          ? `supported by ${independentSourceCount} independent sources`
          : "supported by relevant retrieved evidence",
    };
  }

  return {
    level: "low" as const,
    label: "Low confidence",
    basis:
      "limited or weakly relevant supporting evidence",
  };
}

function mapFindings(
  result: ApiResearchResult,
): Finding[] {
  return result.claims.map((claim, index) => {
    const sortedEvidence = [
      ...claim.evidence,
    ].sort(
      (left, right) =>
        right.relevance - left.relevance,
    );

    const reviewState = mapReviewState(
      claim.review_status,
    );

    return {
      id: `finding-${index + 1}`,
      claim: claim.statement,
      confidence: mapConfidence(claim),
      surfacedBy: "Research Agent",
      verifiedBy: "Claim Verifier",
      evidence: sortedEvidence.map(
        (evidence, evidenceIndex) => ({
          id: `finding-${index + 1}-evidence-${
            evidenceIndex + 1
          }`,
          source: evidence.source.title,
          excerpt: evidence.excerpt,
          relevance: evidence.relevance,
        }),
      ),
      review: {
        state: reviewState,
        note: buildReviewNote(
          claim.review_status,
        ),
      },
    };
  });
}

function toResearchRun(
  response: WorkspaceResponse,
): ResearchRun {
  return {
    id: "LIVE-RUN",
    question: response.result.question,
    status: mapExecutionStatus(
      response.execution.status,
    ),
    sourceCount:
      response.result.sources.length,
    agentCount:
      response.agents.length,
    durationSeconds:
      response.observation
        ?.duration_seconds ?? 0,
    findings: mapFindings(
      response.result,
    ),
    agentTrace: mapAgentTrace(
      response.agents.length > 0,
    ),
    evaluation: mapEvaluation(
      response.evaluation,
    ),
  };
}

export async function fetchRun(
  question: string,
  maxSources = 5,
): Promise<ResearchRun> {
  const trimmedQuestion =
    question.trim();

  if (!trimmedQuestion) {
    throw new Error(
      "Research question must not be empty.",
    );
  }

  const searchParams = new URLSearchParams({
    question: trimmedQuestion,
    max_sources: String(maxSources),
  });

  const response = await fetch(
    `http://127.0.0.1:8000/workspace?${searchParams.toString()}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    let message =
      `Research request failed (${response.status}).`;

    try {
      const body = (await response.json()) as {
        detail?: string;
      };

      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP status message.
    }

    throw new Error(message);
  }

  const data =
    (await response.json()) as WorkspaceResponse;

  return toResearchRun(data);
}