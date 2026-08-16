import {
  useMemo,
  useState,
} from "react";
import type { FormEvent } from "react";

import { fetchRun } from "./api";
import type {
  Finding,
  ResearchRun,
  ReviewState,
} from "./types";

function ThreadNode({
  tone = "neutral",
  filled = false,
}: {
  tone?: "neutral" | "signal" | "review";
  filled?: boolean;
}) {
  const toneClasses = {
    neutral: "border-slate-300 bg-white",
    signal: "border-signal bg-signal",
    review: "border-review bg-review",
  };

  return (
    <span
      aria-hidden="true"
      className={[
        "relative z-10 block h-3 w-3 shrink-0 rounded-full border-2",
        toneClasses[tone],
        filled
          ? "shadow-[0_0_0_3px_rgba(22,124,128,0.10)]"
          : "",
      ].join(" ")}
    />
  );
}

function EvidenceThread({
  finding,
}: {
  finding: Finding;
}) {
  const isPending =
    finding.review.state === "pending";

  const isRejected =
    finding.review.state === "rejected";

  const reviewTone: "signal" | "review" =
    isPending || isRejected
      ? "review"
      : "signal";

  const reviewLabel =
    finding.review.state === "pending"
      ? "Needs human review"
      : finding.review.state === "approved"
        ? "Approved"
        : finding.review.state === "rejected"
          ? "Rejected"
          : "System supported";

  const steps: Array<{
    label: string;
    tone: "neutral" | "signal" | "review";
  }> = [
    {
      label: finding.surfacedBy,
      tone: "signal",
    },
    {
      label: `${finding.evidence.length} ${
        finding.evidence.length === 1
          ? "source"
          : "sources"
      }`,
      tone: "neutral",
    },
    {
      label: finding.verifiedBy,
      tone: "signal",
    },
    {
      label: reviewLabel,
      tone: reviewTone,
    },
  ];

  return (
    <div
      aria-label="Evidence provenance"
      className="flex min-w-0 flex-col items-start"
    >
      {steps.map((step, index) => (
        <div
          key={`${step.label}-${index}`}
          className="flex min-w-0 items-start gap-2"
        >
          <div className="flex flex-col items-center">
            <ThreadNode
              tone={step.tone}
              filled={
                index === 0 ||
                index === steps.length - 1
              }
            />

            {index < steps.length - 1 && (
              <span
                aria-hidden="true"
                className="my-1 h-7 w-px bg-slate-200"
              />
            )}
          </div>

          <span className="max-w-[120px] break-words pt-0.5 font-sans text-[10px] leading-4 text-slate-500">
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function ReviewStateBadge({
  state,
}: {
  state: ReviewState;
}) {
  const config: Record<
    ReviewState,
    {
      label: string;
      className: string;
    }
  > = {
    "system-supported": {
      label: "System supported",
      className:
        "bg-signal-soft text-signal ring-1 ring-signal-line",
    },

    pending: {
      label: "Needs human review",
      className:
        "bg-review-soft text-review-dark ring-1 ring-review-line",
    },

    approved: {
      label: "Approved in session",
      className:
        "bg-signal-soft text-signal ring-1 ring-signal-line",
    },

    rejected: {
      label: "Rejected",
      className:
        "bg-danger-soft text-danger ring-1 ring-red-200",
    },
  };

  return (
    <span
      className={[
        "inline-flex rounded-full px-2.5 py-1",
        "text-[10px] font-semibold tracking-[0.03em]",
        config[state].className,
      ].join(" ")}
    >
      {config[state].label}
    </span>
  );
}

function FindingCard({
  finding,
  reviewState,
  onApprove,
  onReject,
}: {
  finding: Finding;
  reviewState: ReviewState;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [acting, setActing] = useState(false);

  const currentFinding = useMemo(
    () => ({
      ...finding,
      review: {
        ...finding.review,
        state: reviewState,
      },
    }),
    [finding, reviewState],
  );

  async function handleApprove() {
    if (acting) {
      return;
    }

    setActing(true);

    try {
      await onApprove();
    } finally {
      setActing(false);
    }
  }

  async function handleReject() {
    if (acting) {
      return;
    }

    setActing(true);

    try {
      await onReject();
    } finally {
      setActing(false);
    }
  }

  const canReview =
    reviewState === "pending";

  return (
    <article className="grid gap-5 rounded-panel bg-white p-5 shadow-subtle ring-1 ring-slate-200/80 sm:p-6 md:grid-cols-[128px_minmax(0,1fr)] md:gap-6">
      <EvidenceThread finding={currentFinding} />

      <div className="min-w-0">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <ReviewStateBadge
            state={reviewState}
          />

          <span className="font-mono text-[10px] uppercase tracking-[0.06em] text-slate-400">
            relevance-ranked
          </span>
        </div>

        <h3 className="mt-4 max-w-3xl font-prose text-[21px] font-medium leading-[1.5] tracking-[-0.01em] text-ink sm:text-[23px]">
          {finding.claim}
        </h3>

        <div className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className="text-xs font-semibold text-signal">
            {finding.confidence.label}
          </span>

          <span
            aria-hidden="true"
            className="text-xs text-slate-300"
          >
            ·
          </span>

          <span className="text-xs text-slate-500">
            {finding.confidence.basis}
          </span>
        </div>

        <div className="mt-5 rounded-control bg-slate-50 px-4 py-3 ring-1 ring-slate-200/70">
          <p className="text-sm leading-6 text-slate-600">
            {finding.review.note}
          </p>
        </div>

        <div className="mt-5">
          <button
            type="button"
            aria-expanded={open}
            aria-controls={`${finding.id}-evidence`}
            onClick={() =>
              setOpen((current) => !current)
            }
            className={[
              "rounded-md px-1 py-1",
              "text-xs font-semibold text-signal",
              "outline-none ring-offset-2",
              "transition-colors motion-reduce:transition-none",
              "hover:text-signal-dark",
              "focus-visible:ring-2 focus-visible:ring-signal",
            ].join(" ")}
          >
            {open
              ? "Hide evidence trail"
              : "Inspect evidence trail"}
          </button>
        </div>

        {open && (
          <div
            id={`${finding.id}-evidence`}
            className="mt-4 space-y-3 border-l-2 border-signal-line pl-5"
          >
            {finding.evidence.map((evidence) => (
              <div
                key={evidence.id}
                className="rounded-control bg-white p-4 ring-1 ring-slate-200"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-xs font-semibold text-ink">
                    {evidence.source}
                  </h4>

                  <span className="font-mono text-[10px] text-slate-500">
                    relevance{" "}
                    {evidence.relevance.toFixed(
                      2,
                    )}
                  </span>
                </div>

                <p className="mt-2 font-prose text-[14px] leading-6 text-slate-600">
                  {evidence.excerpt}
                </p>
              </div>
            ))}
          </div>
        )}

        {canReview && (
          <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={() =>
                void handleApprove()
              }
              disabled={acting}
              className={[
                "rounded-control bg-signal px-3 py-2",
                "text-xs font-semibold text-white",
                "outline-none ring-offset-2",
                "transition-colors motion-reduce:transition-none",
                "hover:bg-signal-dark",
                "focus-visible:ring-2 focus-visible:ring-signal",
                "disabled:cursor-not-allowed disabled:opacity-60",
              ].join(" ")}
            >
              {acting
                ? "Saving…"
                : "Approve"}
            </button>

            <button
              type="button"
              onClick={() =>
                void handleReject()
              }
              disabled={acting}
              className={[
                "rounded-control bg-white px-3 py-2",
                "text-xs font-semibold text-review-dark",
                "ring-1 ring-review-line",
                "outline-none ring-offset-2",
                "transition-colors motion-reduce:transition-none",
                "hover:bg-review-soft",
                "focus-visible:ring-2 focus-visible:ring-review",
                "disabled:cursor-not-allowed disabled:opacity-60",
              ].join(" ")}
            >
              {acting
                ? "Saving…"
                : "Send back"}
            </button>
          </div>
        )}

        {reviewState ===
          "system-supported" && (
          <div className="mt-5 rounded-control bg-signal-soft px-4 py-3 text-xs font-medium text-signal">
            The automated review policy found sufficient
            support. No human review is currently required.
          </div>
        )}

        {reviewState === "approved" && (
          <div className="mt-5 rounded-control bg-signal-soft px-4 py-3 text-xs font-medium text-signal">
            This finding was approved in the current session.
          </div>
        )}

        {reviewState === "rejected" && (
          <div className="mt-5 rounded-control bg-danger-soft px-4 py-3 text-xs font-medium text-danger">
            This finding was rejected and requires revision before
            another review.
          </div>
        )}
      </div>
    </article>
  );
}

function AgentTrace({
  trace,
}: {
  trace: ResearchRun["agentTrace"];
}) {
  return (
    <section className="rounded-panel bg-white p-5 ring-1 ring-slate-200/80">
      <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
        Run trace
      </div>

      <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
        Agent activity
      </h2>

      <div className="mt-5">
        {trace.map((step, index) => (
          <div
            key={step.id}
            className="relative flex gap-3 pb-5 last:pb-0"
          >
            {index < trace.length - 1 && (
              <span
                aria-hidden="true"
                className="absolute left-[4px] top-3 bottom-0 w-px bg-slate-200"
              />
            )}

            <span
              aria-hidden="true"
              className="relative mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-signal ring-4 ring-signal-soft"
            />

            <div className="min-w-0">
              <div className="font-sans text-xs font-semibold text-ink">
                {step.agent}
              </div>

              <div className="mt-0.5 font-sans text-[11px] leading-5 text-slate-500">
                {step.action}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function HumanCheckpoint({
  finding,
  reviewState,
  onApprove,
  onReject,
}: {
  finding: Finding;
  reviewState: ReviewState;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}) {
  if (reviewState === "pending") {
    return (
      <section className="rounded-panel bg-review-soft p-5 ring-1 ring-review-line">
        <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-review-dark">
          Human checkpoint
        </div>

        <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
          Finding needs review
        </h2>

        <p className="mt-3 font-sans text-xs leading-5 text-review-dark/90">
          The backend review policy flagged this finding. A human
          decision is required before treating it as approved.
        </p>

        <div className="mt-4 rounded-control bg-white/70 p-3 font-sans text-xs text-review-dark">
          "{finding.claim.slice(
            0,
            150,
          )}
          {finding.claim.length > 150
            ? "…"
            : ""}
          "
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() =>
              void onApprove()
            }
            className="rounded-control bg-signal px-3 py-2 text-xs font-semibold text-white outline-none ring-offset-2 hover:bg-signal-dark focus-visible:ring-2 focus-visible:ring-signal"
          >
            Approve
          </button>

          <button
            type="button"
            onClick={() =>
              void onReject()
            }
            className="rounded-control bg-white px-3 py-2 text-xs font-semibold text-review-dark ring-1 ring-review-line outline-none ring-offset-2 hover:bg-review-soft focus-visible:ring-2 focus-visible:ring-review"
          >
            Send back
          </button>
        </div>
      </section>
    );
  }

  if (reviewState === "approved") {
    return (
      <section className="rounded-panel bg-signal-soft p-5 ring-1 ring-signal-line">
        <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-signal">
          Human checkpoint
        </div>

        <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
          Approved in session
        </h2>

        <p className="mt-3 font-sans text-xs leading-5 text-slate-600">
          This finding has an approved review state in the current
          workflow.
        </p>
      </section>
    );
  }

  if (reviewState === "rejected") {
    return (
      <section className="rounded-panel bg-danger-soft p-5 ring-1 ring-red-200">
        <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-danger">
          Human checkpoint
        </div>

        <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
          Changes required
        </h2>

        <p className="mt-3 font-sans text-xs leading-5 text-slate-600">
          This finding is rejected and should be revised before
          another review decision.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-panel bg-slate-50 p-5 ring-1 ring-slate-200">
      <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">
        Review state
      </div>

      <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
        No human checkpoint required
      </h2>

      <p className="mt-3 font-sans text-xs leading-5 text-slate-600">
        The backend review policy marked the selected finding as
        system-supported.
      </p>
    </section>
  );
}

function EvaluationPanel({
  metrics,
}: {
  metrics: ResearchRun["evaluation"];
}) {
  return (
    <section className="rounded-panel bg-white p-5 ring-1 ring-slate-200/80">
      <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
        Evaluation
      </div>

      <h2 className="mt-1 font-sans text-sm font-semibold text-ink">
        How this run was measured
      </h2>

      <div className="mt-5 space-y-6">
        {metrics.map((metric) => (
          <div key={metric.id}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-sans text-xs font-semibold text-ink">
                {metric.label}
              </span>

              <span className="font-mono text-sm font-semibold text-signal">
                {metric.value.toFixed(2)}
              </span>
            </div>

            <p className="mt-2 font-sans text-[11px] leading-5 text-slate-500">
              {metric.method}
            </p>

            {metric.measures.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {metric.measures.map(
                  (measure) => (
                    <span
                      key={measure}
                      className="rounded-full bg-slate-100 px-2 py-1 font-sans text-[10px] text-slate-600"
                    >
                      {measure}
                    </span>
                  ),
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="rounded-panel bg-white px-6 py-12 text-center ring-1 ring-slate-200/80 sm:py-16">
      <div className="mx-auto max-w-xl">
        <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
          Research workspace
        </div>

        <h2 className="mt-3 font-prose text-[26px] font-medium leading-[1.3] tracking-[-0.01em] text-ink sm:text-[30px]">
          Ask a question worth investigating.
        </h2>

        <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-500">
          ResearchOS retrieves evidence, evaluates the resulting
          claims, and exposes where the answer came from.
        </p>
      </div>
    </section>
  );
}

function ResearchForm({
  question,
  onQuestionChange,
  onSubmit,
  loading,
}: {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: (
    event: FormEvent<HTMLFormElement>,
  ) => void;
  loading: boolean;
}) {
  return (
    <form
      onSubmit={onSubmit}
      className="mb-7"
    >
      <label
        htmlFor="research-question"
        className="block font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400"
      >
        Research question
      </label>

      <div className="mt-2 flex flex-col gap-2.5 sm:flex-row">
        <input
          id="research-question"
          name="question"
          type="text"
          value={question}
          onChange={(event) =>
            onQuestionChange(
              event.target.value,
            )
          }
          placeholder="What do you want to research?"
          autoComplete="off"
          spellCheck="true"
          required
          disabled={loading}
          className={[
            "min-h-11 min-w-0 flex-1 rounded-control",
            "bg-white px-4 py-3",
            "text-sm text-ink placeholder:text-slate-400",
            "ring-1 ring-slate-300/90",
            "outline-none ring-offset-2",
            "transition-colors motion-reduce:transition-none",
            "focus-visible:ring-2 focus-visible:ring-signal",
            "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400",
          ].join(" ")}
        />

        <button
          type="submit"
          disabled={
            loading ||
            !question.trim()
          }
          className={[
            "min-h-11 rounded-control px-5 py-3",
            "bg-ink text-xs font-semibold text-white",
            "outline-none ring-offset-2",
            "transition-colors motion-reduce:transition-none",
            "hover:bg-ink-soft",
            "focus-visible:ring-2 focus-visible:ring-signal",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "sm:min-w-32",
          ].join(" ")}
        >
          {loading
            ? "Researching…"
            : "Run Research"}
        </button>
      </div>
    </form>
  );
}

function LoadingState({
  question,
}: {
  question: string;
}) {
  return (
    <section
      aria-live="polite"
      className="rounded-panel bg-white p-6 ring-1 ring-slate-200/80"
    >
      <div className="flex items-center gap-2">
        <span
          aria-hidden="true"
          className="h-2.5 w-2.5 animate-pulse rounded-full bg-signal motion-reduce:animate-none"
        />

        <span className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-signal">
          Research in progress
        </span>
      </div>

      <h2 className="mt-3 font-prose text-xl font-medium text-ink">
        Investigating your question
      </h2>

      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
        "{question}"
      </p>

      <div className="mt-6 space-y-3">
        <div className="h-3 w-2/3 animate-pulse rounded bg-slate-100 motion-reduce:animate-none" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-slate-100 motion-reduce:animate-none" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100 motion-reduce:animate-none" />
      </div>
    </section>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <section
      role="alert"
      className="rounded-panel bg-white p-6 ring-1 ring-red-200"
    >
      <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-danger">
        Research failed
      </div>

      <h2 className="mt-2 font-sans text-base font-semibold text-ink">
        The research run could not be completed
      </h2>

      <p className="mt-2 text-sm leading-6 text-slate-600">
        {message}
      </p>

      <button
        type="button"
        onClick={onRetry}
        className={[
          "mt-5 rounded-control px-4 py-2.5",
          "bg-ink text-xs font-semibold text-white",
          "outline-none ring-offset-2",
          "hover:bg-ink-soft",
          "focus-visible:ring-2 focus-visible:ring-signal",
        ].join(" ")}
      >
        Try again
      </button>
    </section>
  );
}

function Workspace({
  run,
}: {
  run: ResearchRun;
}) {
  const [reviewStates, setReviewStates] =
    useState<Record<string, ReviewState>>(
      () =>
        Object.fromEntries(
          run.findings.map(
            (finding) => [
              finding.id,
              finding.review.state,
            ],
          ),
        ) as Record<
          string,
          ReviewState
        >,
    );

  const pendingFinding =
    run.findings.find(
      (finding) =>
        reviewStates[finding.id] ===
        "pending",
    ) ?? null;

  const checkpointFinding =
    pendingFinding ?? run.findings[0];

  async function approveFinding(
    findingId: string,
  ) {
    setReviewStates((current) => ({
      ...current,
      [findingId]: "approved",
    }));
  }

  async function rejectFinding(
    findingId: string,
  ) {
    setReviewStates((current) => ({
      ...current,
      [findingId]: "rejected",
    }));
  }

  return (
    <section>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
            Findings
          </div>

          <h2 className="mt-1 font-sans text-lg font-semibold tracking-[-0.02em]">
            Evidence-backed findings
          </h2>
        </div>

        <div className="font-mono text-[10px] text-slate-400">
          {run.findings.length}{" "}
          {run.findings.length === 1
            ? "finding"
            : "findings"}
        </div>
      </div>

      <div className="space-y-4">
        {run.findings.map(
          (finding) => (
            <FindingCard
              key={finding.id}
              finding={finding}
              reviewState={
                reviewStates[
                  finding.id
                ] ??
                finding.review.state
              }
              onApprove={() =>
                approveFinding(
                  finding.id,
                )
              }
              onReject={() =>
                rejectFinding(
                  finding.id,
                )
              }
            />
          ),
        )}
      </div>

      <div className="mt-6 grid gap-4">
        <AgentTrace
          trace={run.agentTrace}
        />

        {checkpointFinding && (
          <HumanCheckpoint
            finding={checkpointFinding}
            reviewState={
              reviewStates[
                checkpointFinding.id
              ] ??
              checkpointFinding.review.state
            }
            onApprove={() =>
              approveFinding(
                checkpointFinding.id,
              )
            }
            onReject={() =>
              rejectFinding(
                checkpointFinding.id,
              )
            }
          />
        )}

        <EvaluationPanel
          metrics={run.evaluation}
        />
      </div>
    </section>
  );
}

function App() {
  const [question, setQuestion] =
    useState("");

  const [run, setRun] =
    useState<ResearchRun | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [
    submittedQuestion,
    setSubmittedQuestion,
  ] = useState("");

  async function runResearch(
    nextQuestion: string,
  ) {
    const trimmedQuestion =
      nextQuestion.trim();

    if (
      !trimmedQuestion ||
      loading
    ) {
      return;
    }

    setLoading(true);
    setError(null);
    setRun(null);
    setSubmittedQuestion(
      trimmedQuestion,
    );

    try {
      const result =
        await fetchRun(
          trimmedQuestion,
          5,
        );

      setRun(result);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to complete the research run.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    void runResearch(question);
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="mx-auto w-[min(1280px,calc(100%-24px))] py-6 sm:w-[min(1280px,calc(100%-40px))] sm:py-7">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid h-8 w-8 place-items-center rounded-[8px] bg-ink text-sm font-bold text-white">
              R
            </div>

            <div>
              <div className="font-sans text-sm font-semibold">
                ResearchOS
              </div>

              <div className="font-sans text-[11px] text-slate-500">
                Evidence-grounded research
              </div>
            </div>
          </div>

          <div className="font-mono text-[10px] tracking-[0.06em] text-slate-400">
            {run
              ? `${run.id} · ${run.status.toUpperCase()}`
              : "READY"}
          </div>
        </header>

        <section className="mb-6">
          <div className="mb-6">
            <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
              Research workspace
            </div>

            <h1 className="mt-2 max-w-3xl font-prose text-[30px] font-medium leading-[1.25] tracking-[-0.015em] sm:text-[36px]">
              Research a question. Inspect the evidence.
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
              ResearchOS retrieves sources, builds
              evidence-backed findings, evaluates the run,
              and exposes the reasoning path instead of
              hiding it behind a single answer.
            </p>
          </div>

          <ResearchForm
            question={question}
            onQuestionChange={
              setQuestion
            }
            onSubmit={handleSubmit}
            loading={loading}
          />
        </section>

        {loading && (
          <LoadingState
            question={
              submittedQuestion
            }
          />
        )}

        {!loading && error && (
          <ErrorState
            message={error}
            onRetry={() =>
              void runResearch(
                submittedQuestion,
              )
            }
          />
        )}

        {!loading &&
          !error &&
          !run && (
            <EmptyState />
          )}

        {!loading &&
          !error &&
          run && (
            <>
              <section className="mb-6 rounded-panel bg-white px-5 py-6 ring-1 ring-slate-200/80 sm:px-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                      Research result
                    </div>

                    <h2 className="mt-2 max-w-4xl font-prose text-[27px] font-medium leading-[1.3] tracking-[-0.012em] sm:text-[31px]">
                      {run.question}
                    </h2>
                  </div>

                  <div className="flex flex-wrap gap-2 font-sans text-[11px] text-slate-500">
                    <span className="rounded-full bg-slate-100 px-2.5 py-1">
                      {run.sourceCount} sources
                    </span>

                    <span className="rounded-full bg-slate-100 px-2.5 py-1">
                      {run.agentCount} agents
                    </span>

                    <span className="rounded-full bg-slate-100 px-2.5 py-1">
                      {run.durationSeconds > 0
                        ? `${run.durationSeconds.toFixed(1)}s`
                        : "completed"}
                    </span>
                  </div>
                </div>
              </section>

              <Workspace run={run} />
            </>
          )}
      </div>
    </main>
  );
}

export default App;