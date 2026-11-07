import { useEffect, useState } from "react";
import { api, pretty } from "../api";
import type { RecordData as R } from "../api";
import type { Common } from "../types";
import { Badge, Json, Empty, Editor } from "../components";
import { defaultSettings } from "../constants";

export function Experiments(p: Common) {
  const [showTerminated, setShowTerminated] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [jobSearch, setJobSearch] = useState("");
  const visibleJobs = [...p.jobs].reverse().filter(job => Boolean(job.archived) === showArchived
    && (showArchived || showTerminated || job.status !== "terminated")
    && `${job.name} ${job.id} ${job.kind} ${job.status}`.toLowerCase().includes(jobSearch.toLowerCase()));
  const [name, setName] = useState("Reflection collection"), [ds, setDs] = useState(""), [bank, setBank] = useState(""), [split, setSplit] = useState("development");
  const [reps, setReps] = useState(1), [selected, setSelected] = useState(""), [outputs, setOutputs] = useState<R[]>([]);
  const [methods, setMethods] = useState(["fixed"]), [models, setModels] = useState<string[]>([]);
  const [settings, setSettings] = useState(pretty(defaultSettings)), [mode, setMode] = useState("short"), [topK, setTopK] = useState(3);
  const [preflight, setPreflight] = useState<R | null>(null);
  const usesBank = methods.some(m => m === "fixed" || m === "rag");
  const usesModel = methods.some(m => m !== "fixed");
  const toggle = (values: string[], value: string) => values.includes(value) ? values.filter(v => v !== value) : [...values, value];
  const configuration = () => ({name, dataset_snapshot_id:ds, bank_snapshot_id:usesBank ? bank : null, split, methods, models:usesModel ? models : [], repetitions:reps, ai_control:false, settings:JSON.parse(settings), mode, top_k:topK});
  const selectedBankSnapshot = p.snapshots.find(s => s.id === bank);
  const invalidExperimental = usesBank && selectedBankSnapshot?.review_mode === "experimental" && split !== "development";
  useEffect(() => {
    let active = true;
    setOutputs([]);
    if (selected) api("/outputs?job_id=" + selected).then(rows => {if (active) setOutputs(rows);});
    return () => {active = false;};
  }, [selected, p.revision]);
  return (<>
      <section className="card">
        <h2>Collect reflection questions</h2>
        <p>Choose bank selection, RAG or LLM generation. The experiment only collects results; evaluation runs separately using fixed scripts. With 30 scenarios, all three methods and one generator, one repetition collects 90 results.</p>
        <div className="form-grid">
          <label>Experiment name<input value={name} onChange={e => setName(e.target.value)} /></label>
          <label>Dataset snapshot<select aria-label="Dataset snapshot" value={ds} onChange={e => setDs(e.target.value)}>
            <option value="">Select frozen dataset</option>
            {p.snapshots.filter(s => s.kind === "dataset").map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select></label>
          <label>Split<select value={split} onChange={e => setSplit(e.target.value)}>{["development", "validation", "test"].map(s => <option key={s}>{s}</option>)}</select></label>
          <label>Question-bank snapshot<select aria-label="Question-bank snapshot" disabled={!usesBank} value={bank} onChange={e => setBank(e.target.value)}>
            <option value="">Select a bank snapshot</option>
            {p.snapshots.filter(s => s.kind === "bank").map(s => <option key={s.id} value={s.id}>{s.bank_name || "Default bank"} / {s.name} / {s.review_mode === "experimental" ? "EXPERIMENTAL" : "Approved only"}</option>)}
          </select></label>
          <label>Repetitions<input type="number" min={1} max={100} value={reps} onChange={e => setReps(+e.target.value)} /></label>
        </div>
        <fieldset><legend>Collection methods</legend>{[["fixed", "Fixed question bank"], ["rag", "Retrieval-augmented generation"], ["constrained", "Constrained LLM"]].map(([id, title]) => <label className="check" key={id}><input type="checkbox" checked={methods.includes(id)} onChange={() => setMethods(toggle(methods, id))} />{title}</label>)}</fieldset>
        {usesModel && <>
          <fieldset><legend>Local models for collecting questions</legend>{!p.modelState.models.length && <p>No installed local models available. Check Models.</p>}{p.modelState.models.map((model: R) => <label className="check" key={model.name}><input type="checkbox" checked={models.includes(model.name)} onChange={() => setModels(toggle(models, model.name))} />{model.name} / {model.identity?.variant || "Variant unknown"}</label>)}</fieldset>
          <label>Research inference mode<select aria-label="Research inference mode" value={mode} onChange={e => setMode(e.target.value)}><option value="short">Short non-thinking generation</option><option value="thinking">Intentional thinking experiment</option></select></label>
          <details><summary>Generation settings</summary><Editor label="Generation settings (JSON)" value={settings} set={setSettings} rows={9} /><label>Retrieval top k<input type="number" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} /></label></details>
          <button disabled={p.busy || !ds || invalidExperimental} onClick={() => p.run(async () => setPreflight(await api("/experiments/preflight", "POST", configuration())), "Collection preflight finished; no AI evaluation was run.")}>Run research preflight</button>
          {preflight && <details open><summary>Collection preflight: {preflight.passed ? "passed" : "failed"}</summary><p>Required for batches over 10 model-generated cases. Changing models, snapshots or settings requires a new preflight.</p><Json value={preflight} /></details>}
        </>}
        {invalidExperimental && <p className="error-text">Experimental bank snapshots require the development split.</p>}
        {reps > 1 && methods.includes("fixed") && <p>Fixed selection repeats the same decision for identical inputs; its repetitions do not add independent evidence.</p>}
        <p className="note">First collect all questions. Then select Run fixed metrics in Evaluation, Metrics or the completed experiment below. No AI evaluator is used.</p>
        <button className="primary" disabled={p.busy || !ds || (usesBank && !bank) || !methods.length || (usesModel && !models.length) || invalidExperimental} onClick={() => p.run(async () => {
          const job = await api("/experiments", "POST", {...configuration(), preflight_id:preflight?.id || null});
          setSelected(job.id);
        }, "Experiment queued. Questions are collected without AI evaluation.")}>Queue experiment</button>
      </section>
      <section className="card">
        <h2>Persistent jobs</h2>
        <label className="check"><input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} />Archived jobs ({p.jobs.filter((job) => job.archived).length})</label>
        <label>Find job<input aria-label="Find job" value={jobSearch} onChange={(e) => setJobSearch(e.target.value)} placeholder="Name, ID or status" /></label>
        <label className="check"><input type="checkbox" checked={showTerminated} onChange={(e) => setShowTerminated(e.target.checked)} />Show terminated jobs</label>
        {!p.jobs.length && <Empty>No experiments or scenario tasks yet.</Empty>}
        {p.jobs.length > 0 && !visibleJobs.length && <Empty>No jobs in this view. Use Archived jobs or Show terminated jobs to find retained history.</Empty>}
        {visibleJobs.map((j) => (
          <div className="job" key={j.id}>
            <div className="row spread">
              <button className="text" onClick={() => setSelected(j.id)}>
                <b>{j.name}</b>
              </button>
              <Badge status={j.status}>{j.status}</Badge>
            </div>
            <small>
              {j.id} · {j.kind} · {j.kind === "question_generation" ? `Requested ${j.total} · Saved ${j.saved_count ?? j.done} · Failed ${j.failed_count ?? 0} · Pending ${j.pending_count ?? j.total - j.done}` : `${j.done}/${j.total} finished`}
            </small>
            <progress value={j.done} max={j.total || 1} />
            {j.error && <p className="error-text">{j.error}</p>}
            {j.kind === "evaluation" && <p>{j.assessed_count || 0} assessments saved · {j.failed_count || 0} failed · {j.skipped_count || 0} skipped · exact output versions retained. {j.bias_flags?.join("; ")}</p>}
            {j.generation_summary && <details><summary>Scenario generation coverage and warnings</summary><Json value={j.generation_summary} /></details>}
            {j.bank_snapshot_id && <p>Bank snapshot: {j.bank_snapshot?.bank_name || p.snapshots.find((snapshot) => snapshot.id === j.bank_snapshot_id)?.bank_name || "Default bank"} · {j.bank_snapshot_id} · {(j.bank_snapshot?.review_mode || p.snapshots.find((snapshot) => snapshot.id === j.bank_snapshot_id)?.review_mode) === "experimental" ? "EXPERIMENTAL — development only" : "Approved only"} · <code>{j.bank_snapshot?.content_hash?.slice(0, 16)}</code></p>}
            {(j.scenario_attempts || j.question_attempts)?.length > 0 && <details>
              <summary>{j.kind === "question_generation" ? "Question" : "Scenario"} generation attempts ({(j.scenario_attempts || j.question_attempts).length})</summary>
              <p>Valid drafts are retained. Each new draft requires human review. Inspect execution for prompts, schema, raw responses and effective settings.</p>
              {(j.scenario_attempts || j.question_attempts).map((attempt: R, i: number) => <div key={i}>
                <b>Item {attempt.sequence} · Attempt {attempt.attempt || "legacy"} · {attempt.status}</b>
                {attempt.errors?.map((error: R, k: number) => <p key={k} className="error-text">{error.path}: {error.message} ({error.type})</p>)}
              </div>)}
            </details>}
            <div className="actions">
              {j.kind === "experiment" && ["completed", "completed_with_errors"].includes(j.status) && <button disabled={p.busy} onClick={() => p.run(() => api(`/jobs/${j.id}/script-evaluation`, "POST", {}), "Fixed metrics saved. Open Metrics for the results.")}>Run fixed metrics</button>}

              {["completed", "completed_with_errors", "failed", "cancelled", "interrupted", "terminated"].includes(j.status) && <button disabled={p.busy} onClick={() => p.run(async () => {
                await api(`/jobs/${j.id}/${j.archived ? "unarchive" : "archive"}`, "POST", {});
                if (selected === j.id) { setSelected(""); setOutputs([]); }
              }, j.archived ? "Job restored to the main list." : "Job archived. Find it under Archived jobs; all records are retained.")}>{j.archived ? "Restore job" : "Archive job"}</button>}
              {["queued", "failed", "cancelled", "interrupted"].includes(j.status) && <button disabled={p.busy} onClick={() => p.run(async () => {
                await api(`/jobs/${j.id}/terminate`, "POST", {});
                if (selected === j.id) { setSelected(""); setOutputs([]); }
              }, "Job terminated and removed from the queue. Results and diagnostics are retained under Show terminated jobs.")}>{j.status === "queued" ? "Remove from queue" : "Terminate job"}</button>}
              {j.status === "terminated" && <p>Terminated. Results and diagnostics are retained; this job cannot be resumed.</p>}
              {j.status === "running" && (
                <button
                  disabled={p.busy}
                  onClick={() =>
                    p.run(
                      () => api(`/jobs/${j.id}/cancel`, "POST", {}),
                      "Cancellation requested; partial records are retained.",
                    )
                  }
                >
                  Cancel job
                </button>
              )}
              {j.kind !== "evaluation" && !j.config?.ai_control && ["interrupted", "cancelled", "failed", "completed_with_errors"].includes(j.status) && (
                <button
                  disabled={p.busy}
                  onClick={() =>
                    p.run(
                      () => api(`/jobs/${j.id}/resume`, "POST", {}),
                      "Job resumed; finalized outputs will not be regenerated.",
                    )
                  }
                >
                  Resume remaining work
                </button>
              )}
              <a className="button" href={`/api/jobs/${j.id}/export`}>
                Export records
              </a>
              <button onClick={() => setSelected(j.id)}>
                Inspect execution
              </button>
            </div>
            {j.results?.length > 0 && (
              <p>Candidate {j.kind === "question_generation" ? "question" : "scenario"} versions: {j.results.join(", ")}</p>
            )}
          </div>
        ))}
      </section>
      {selected && (
        <section className="card">
          <h2>Inspectable execution records</h2>
          <p>{selected}</p>
          <details>
            <summary>Experiment configuration & model metadata</summary>
            <Json value={p.jobs.find((j) => j.id === selected)} />
          </details>
          {outputs.map((o) => (
            <details key={o.id}>
              <summary>
                {o.status} · {o.method} · {o.model || "Not applicable"} ·{" "}
                {o.question || o.error || "Waiting"}
              </summary>
              <Json value={o} />
            </details>
          ))}
        </section>
      )}
    </>
  );
}
