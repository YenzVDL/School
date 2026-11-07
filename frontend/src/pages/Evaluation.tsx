import { useEffect, useState } from "react";
import { api } from "../api";
import type { RecordData as R } from "../api";
import type { Common } from "../types";
import { Badge, Json, Empty, InputTable } from "../components";
import { emptyCriterion } from "../constants";

import { ScriptEvaluation } from "./ScriptEvaluation";

const criterionNames: Record<string, string> = {usefulness: "Reflective suitability", context_fit: "ICT context fit", correctness: "Factual correctness"};

export function Evaluation(p: Common) {
  const [sourceJob, setSourceJob] = useState("");
  const [blind, setBlind] = useState(true),
    [seed, setSeed] = useState(42),
    [queue, setQueue] = useState<R[]>([]),
    [index, setIndex] = useState(0),
    [role, setRole] = useState("primary"),
    [judgment, setJudgment] = useState<R>({
      usefulness: emptyCriterion(),
      context_fit: emptyCriterion(),
      correctness: emptyCriterion(),
    }),
    [labels, setLabels] = useState<R[]>([]),
    [refs, setRefs] = useState<string[]>([]);
  useEffect(() => {
    api(`/evaluation-queue?blind=${blind}&order_seed=${seed}${sourceJob ? "&job_id="+sourceJob : ""}`).then(setQueue);
  }, [p.revision, blind, seed, sourceJob]);
  const current = queue[index];
  useEffect(() => {
    setJudgment({
      usefulness: emptyCriterion(),
      context_fit: emptyCriterion(),
      correctness: emptyCriterion(),
    });
    setRefs([]);
    setLabels([]);
    if (current) api("/labels?output_id=" + current.id).then(setLabels);
  }, [current?.id, p.revision]);
  const change = (c: string, k: string, v: unknown) =>
    setJudgment({ ...judgment, [c]: { ...judgment[c], [k]: v } });
  return (
    <>
      <label>Experiment to evaluate<select aria-label="Experiment to evaluate" value={sourceJob} onChange={e => {setSourceJob(e.target.value); setIndex(0);}}>
        <option value="">Select experiment</option>
        {p.jobs.filter(j => j.kind === "experiment").map(j => <option key={j.id} value={j.id}>{j.name} / {j.id}</option>)}
      </select></label>
      <ScriptEvaluation jobId={sourceJob} p={p} />
      <details><summary>Optional manual review and historical judgments</summary>
      <h2>Manual review and comparison</h2>
      <div className="toolbar">
        <label className="check">
          <input
            type="checkbox"
            checked={blind}
            onChange={(e) => setBlind(e.target.checked)}
          />
          Hide model and method identities
        </label>
        <label>
          Randomized order seed
          <input
            type="number"
            value={seed}
            onChange={(e) => {
              setSeed(+e.target.value);
              setIndex(0);
            }}
          />
        </label>
        <Badge>{queue.length} outputs available</Badge>
      </div>
      <p className="lead">
        Assess each exact output version. “Not assessed” is an incomplete review
        state and is never converted to No. Other judgments remain hidden until
        you choose to inspect them.
      </p>
      {!current ? (
        <Empty>
          No finalized questions available. Run an experiment first.
        </Empty>
      ) : (
        <>
          <div className="row spread">
            <button disabled={index === 0} onClick={() => setIndex(index - 1)}>
              ← Previous output
            </button>
            <span>
              Output {index + 1} of {queue.length}
            </span>
            <button
              disabled={index >= queue.length - 1}
              onClick={() => setIndex(index + 1)}
            >
              Next output →
            </button>
          </div>
          <div className="evaluation-layout">
            <section className="card">
              <h2>Available scenario context</h2>
              <InputTable inputs={current.inputs} />
            </section>
            <section className="card">
              <span className="eyebrow">
                REFLECTION QUESTION · OUTPUT V{current.version}
              </span>
              <blockquote>{current.question}</blockquote>
              <small>{current.id}</small>
              <p>Assess this question against the scenario shown here: reflective suitability, alignment with its ICT goal and activity, and whether its assumptions are supported. Missing evidence stays unknown.</p>
              {!blind && (
                <p>
                  Method: {current.method} · Model:{" "}
                  {current.model || "Not applicable"}
                </p>
              )}
              {current.status === "invalid" && (
                <div className="warning">
                  This output failed format or repetition checks. Its record
                  remains part of reporting.
                </div>
              )}
              <label>
                Review role
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="primary">Primary reference review</option>
                  <option value="secondary">
                    Independent second reviewer (optional subset)
                  </option>
                  <option value="adjudication">Adjudication</option>
                </select>
              </label>
              {(["usefulness", "context_fit", "correctness"] as const).map((c) => (
                <fieldset key={c}>
                  <legend>
                    {criterionNames[c]}
                  </legend>
                  <p>
                    {c === "usefulness"
                      ? "Meaningful reflection? Clear, answerable, relevant? Preserves agency without pressure or judgment?"
                      : c === "context_fit" ? "Does the question fit this exact ICT learning goal and activity? Does it use available context without switching to an unrelated technology?"
                      : "Accurate use of available evidence? No invented performance, emotions, causes or circumstances? Handles unknowns and contradictions?"}
                  </p>
                  <label>
                    Judgment
                    <select
                      aria-label={c + " judgment"}
                      value={judgment[c].value || ""}
                      onChange={(e) =>
                        change(c, "value", e.target.value || null)
                      }
                    >
                      <option value="">Not assessed</option>
                      <option>Yes</option>
                      <option>No</option>
                    </select>
                  </label>
                  <label>
                    Short explanation
                    <textarea
                      aria-label={c + " explanation"}
                      value={judgment[c].explanation}
                      onChange={(e) => change(c, "explanation", e.target.value)}
                    />
                  </label>
                  <label>
                    Supporting or conflicting context
                    <textarea
                      aria-label={c + " context"}
                      value={judgment[c].context}
                      onChange={(e) => change(c, "context", e.target.value)}
                    />
                  </label>
                </fieldset>
              ))}
              {role === "adjudication" && (
                <fieldset>
                  <legend>Reference labels from at least two reviewers</legend>
                  {labels
                    .filter(
                      (l) =>
                        l.source === "human" &&
                        l.output_version === current.version &&
                        l.role !== "adjudication",
                    )
                    .map((l) => (
                      <label className="check" key={l.id}>
                        <input
                          type="checkbox"
                          checked={refs.includes(l.id)}
                          onChange={() =>
                            setRefs(
                              refs.includes(l.id)
                                ? refs.filter((v) => v !== l.id)
                                : [...refs, l.id],
                            )
                          }
                        />
                        {l.reviewer} · {l.role} · {l.id}
                      </label>
                    ))}
                </fieldset>
              )}
              <button
                className="primary"
                disabled={!p.reviewer || p.busy}
                onClick={() =>
                  p.run(
                    () =>
                      api("/labels", "POST", {
                        output_id: current.id,
                        output_version: current.version,
                        reviewer: p.reviewer,
                        role,
                        judgment,
                        reference_label_ids: refs,
                      }),
                    "Human judgment saved separately from AI judgments.",
                  )
                }
              >
                Save human evaluation
              </button>
              <details>
                <summary>
                  Inspect existing judgments (may affect blinding)
                </summary>
                <p>AI explanations are model judgments, not proof.</p>
                <p>Active AI assessment is the most recent record for this exact output version. Earlier assessments and human reviews remain stored separately.</p>
                <table><thead><tr><th>Source and reviewer</th><th>Reflective suitability</th><th>ICT context fit</th><th>Factual correctness</th></tr></thead><tbody>{labels.filter((label) => label.output_version === current.version && label.is_active).map((label) => <tr key={label.id}><td>{label.source} · {label.reviewer} · {label.role}</td><td>{label.judgment.usefulness.value || "Not assessed"}</td><td>{label.judgment.context_fit?.value || "Not assessed"}</td><td>{label.judgment.correctness.value || "Not assessed"}</td></tr>)}</tbody></table>
                <Json value={labels} />
              </details>
            </section>
          </div>
        </>
      )}
      </details>
    </>
  );
}

