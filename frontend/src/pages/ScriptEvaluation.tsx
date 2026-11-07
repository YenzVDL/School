import { useEffect, useState } from "react";
import { api, rate, type RecordData as R } from "../api";
import type { Common } from "../types";
import { InputTable, Json, ModelSelect } from "../components";

const names: Record<string,string> = {format:"Mechanical format", reflection_structure:"Question structure", contextual_grounding:"Explicit context references", factual_grounding:"Recognized factual claims", agency_wording:"Agency wording signals", usefulness:"Legacy wording cues", context_fit:"Legacy context rule", correctness:"Legacy factual rule"};
const title = (name:string) => names[name] || name;

function Summary({report}:{report:R}) {
  const op=report.operational;
  return <>
    <p><b>{report.version}</b> - {report.id}</p>
    <p>{report.evaluated}/{report.total} questions evaluated by scripts</p>
    {op ? <p>Planned {op.planned}; successful {op.successful}; execution failures {op.execution_failures}. Format: {op.format_compliant}/{op.format_checked} nonempty outputs ({rate(op.format_rate_per_present)}); {op.format_compliant}/{op.planned} planned ({rate(op.format_rate_per_planned)}).</p>
      : <p>Legacy format rate {rate(report.format_pass_rate)} uses completed outputs only. It is not comparable to the v3 planned-output denominator.</p>}
    <table><thead><tr><th>Scoped indicator</th><th>Pass</th><th>Flag</th><th>Inconclusive</th><th>Skipped</th><th>Decision coverage</th></tr></thead>
      <tbody>{Object.entries(report.criteria).map(([key,value])=>{const c=value as R;return <tr key={key}><td>{title(key)}</td><td>{c.pass}</td><td>{c.flag}</td><td>{c.inconclusive}</td><td>{c.skipped ?? "-"}</td><td>{rate(c.decision_coverage)}</td></tr>;})}</tbody></table>
    <small>Implementation hash: {report.implementation_hash}; batch: {report.batch_hash}; saved: {report.created_at || "offline"}</small>
  </>;
}

export function ScriptEvaluation({jobId,p}:{jobId:string;p:Common}) {
  const [data,setData]=useState<R|null>(null),[error,setError]=useState("");
  const [chosen,setChosen]=useState(""),[comparison,setComparison]=useState("");
  const [method,setMethod]=useState(""),[criterion,setCriterion]=useState(""),[status,setStatus]=useState(""),[reviewOnly,setReviewOnly]=useState(false),[matched,setMatched]=useState(true);
  useEffect(()=>{setChosen("");setComparison("");setMethod("");setCriterion("");setStatus("");},[jobId]);
  useEffect(()=>{
    let active=true;
    setError("");
    if (!jobId){setData(null);return;}
    api(`/jobs/${jobId}/metrics`).then(value=>{if(active)setData({...value,selected_job_id:jobId});}).catch(e=>{if(active)setError(e.message);});
    return ()=>{active=false;};
  },[jobId,p.revision]);
  if(!jobId)return <p>Select an experiment to assess its collected questions.</p>;
  if(error)return <p className="error-text">{error}</p>;
  if(!data || data.selected_job_id!==jobId)return <p>Loading experiment...</p>;
  const evaluation=data.script_evaluation;
  const reports:R[]=evaluation.reports || (evaluation.result?[evaluation.result]:[]);
  const result=(chosen?reports.find(r=>r.id===chosen):evaluation.result || reports.at(-1)) || null;
  const prior=reports.find(r=>r.id===comparison);
  const pairMatches=(pair:R)=>{
    if(method && pair.method!==method)return false;
    if(reviewOnly && pair.review_state!=="requires_review" && pair.status!=="inconclusive")return false;
    if(criterion && !pair.criteria[criterion])return false;
    if(status){const candidates=criterion?[pair.criteria[criterion]]:Object.values(pair.criteria);if(!candidates.some((c:any)=>c?.status===status))return false;}
    return true;
  };
  const pairs:R[]=result?result.pairs.filter(pairMatches):[];
  return <section className="card">
    <h2>Fixed metric scripts</h2>
    <p>Collect all outputs, then run the same deterministic indicators for Fixed bank, RAG and LLM. No semantic judgment is inferred from keywords, word overlap or diversity.</p>
    <p>{data.completion.valid_outputs}/{data.planned} completed questions; {data.completion.execution_failures} execution failures; experiment {data.completion.processing_status}.</p>
    {evaluation.status==="collecting" && <p className="note">Finish collection before evaluation.</p>}
    {evaluation.status==="ready" && <p className="note">Collection is complete. The current rubric has not been run on this batch. Earlier reports remain available below.</p>}
    {evaluation.status==="stale" && <p className="warning">Inputs or implementation changed. The saved report remains accessible; run a new immutable assessment for current inputs.</p>}
    <button className="primary" disabled={p.busy || !evaluation.can_run} onClick={()=>p.run(()=>api(`/jobs/${jobId}/script-evaluation`,"POST",{}),"Fixed metrics saved as a separate report. Original results are preserved.")}>Run fixed metrics</button>
    <a className="button" href={`/api/jobs/${jobId}/export`}>Export results & metrics</a>
    {reports.length>0 && <div className="form-grid">
      <label>Evaluation version / saved report<select aria-label="Evaluation version" value={result?.id || ""} onChange={e=>{setChosen(e.target.value);setCriterion("");if(e.target.value===comparison)setComparison("");}}>{reports.map(r=><option key={r.id} value={r.id}>{r.version} / {r.created_at} / {r.id}</option>)}</select></label>
      <label>Compare with saved report<select aria-label="Compare saved report" value={comparison} onChange={e=>setComparison(e.target.value)}><option value="">No side-by-side comparison</option>{reports.filter(r=>r.id!==result?.id).map(r=><option key={r.id} value={r.id}>{r.version} / {r.id}</option>)}</select></label>
    </div>}
    {result && <>
      <p className="note">Pass: the specified observable rule is supported. Flag: a detected violation. Inconclusive: the rule cannot decide. Skipped: content assessment is unavailable. No overall quality score is computed; broad semantic quality requires a separate review.</p>
      <div className={prior?"form-grid":""}><div><Summary report={result}/><a href={`/api/script-evaluations/${result.id}/export`}>Export this exact report</a></div>{prior && <div><Summary report={prior}/><a href={`/api/script-evaluations/${prior.id}/export`}>Export comparison report</a><p>Rubrics measure different properties. Changes are not improvements in the original model outputs.</p></div>}</div>
      <h3>Compare Fixed bank, RAG and LLM</h3>
      <p>{result.comparison.common_scenario_repetitions} shared scenario/repetition cases; {result.comparison.condition_count} conditions. Method/model metadata is attached after content scoring.</p>
      <label className="check"><input type="checkbox" checked={matched} onChange={e=>setMatched(e.target.checked)}/>Compare matched scenario versions and repetitions</label>
      <table><thead><tr><th>Method / model</th><th>Successful / planned</th>{Object.keys(result.criteria).map(k=><th key={k}>{title(k)}: pass / flag / inconclusive</th>)}<th>Lexical overlap</th><th>Normalized unique</th></tr></thead><tbody>{result.by_condition.map((group:R)=>{const stats=matched?group.matched_cases:group;return <tr key={`${group.method}:${group.model}:${group.condition_id}`}><td>{group.method} / {group.model}</td><td>{stats.evaluated}/{stats.total}</td>{Object.keys(result.criteria).map(k=>{const c=stats.criteria[k];return <td key={k}>{c.pass} / {c.flag} / {c.inconclusive}<br/><small>{rate(c.decision_coverage)} decision coverage</small></td>;})}<td>{rate(stats.context_token_precision_mean)}</td><td>{stats.unique_question_count}</td></tr>;})}</tbody></table>
      <details><summary>Definitions, operational denominators and diversity</summary><p>Lexical overlap and reuse describe the output. Reuse is not an individual error and uniqueness is not a quality reward.</p><Json value={{rules:result.rules,rule_versions:result.rule_versions,operational:result.operational,diversity:result.diversity,word_count:result.word_count,rule_counts:result.rule_counts}}/></details>
      <h3>Inspect individual outputs</h3>
      <div className="form-grid">
        <label>Method filter<select value={method} onChange={e=>setMethod(e.target.value)}><option value="">All methods</option>{[...new Set(result.pairs.map((r:R)=>r.method))].map((m:any)=><option key={m}>{m}</option>)}</select></label>
        <label>Criterion filter<select value={criterion} onChange={e=>setCriterion(e.target.value)}><option value="">All criteria</option>{Object.keys(result.criteria).map(k=><option key={k} value={k}>{title(k)}</option>)}</select></label>
        <label>Status filter<select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{["pass","flag","inconclusive","skipped"].map(s=><option key={s}>{s}</option>)}</select></label>
        <label className="check"><input type="checkbox" checked={reviewOnly} onChange={e=>setReviewOnly(e.target.checked)}/>Cases requiring semantic review</label>
      </div>
      <p>{pairs.length} matching outputs. Human/AI semantic reviews do not alter fixed metrics.</p>
      {pairs.map(pair=>{const old=prior?.pairs.find((r:R)=>r.output_id===pair.output_id && r.output_version===pair.output_version);return <details key={`${pair.output_id}:${pair.output_version}`}>
        <summary>{pair.status} / {pair.method} / {pair.model || "No generator model"} / {pair.question || "No output"}</summary>
        <p>Output {pair.output_id} v{pair.output_version}; scenario {pair.scenario_version_id}; review state {pair.review_state || "legacy"}; rubric {result.version}.</p>
        <blockquote>{pair.question}</blockquote><InputTable inputs={pair.inputs}/>
        <div className={old?"form-grid":""}><div><h4>{result.version}</h4><Json value={{classification:pair.classification,criteria:pair.criteria,checks:pair.checks,measurements:pair.measurements,evidence_conflicts:pair.evidence_conflicts,semantic_quality:pair.semantic_quality}}/></div>{old && <div><h4>{prior?.version}</h4><Json value={{criteria:old.criteria,checks:old.checks,measurements:old.measurements}}/></div>}</div>
      </details>;})}
      <OptionalSemantic p={p} jobId={jobId} pairs={result.pairs}/>
      <details><summary>Existing human review coverage and disagreements</summary><Json value={data.semantic_review_coverage}/><Json value={data.disagreements}/><p>Use the optional manual review section on Evaluation to add evidence-based human judgments. Binary human labels and anchored AI ratings are different instruments; no automatic agreement score combines them.</p></details>
    </>}
  </section>;
}

function OptionalSemantic({p,jobId,pairs}:{p:Common;jobId:string;pairs:R[]}) {
  const [enabled,setEnabled]=useState(false),[model,setModel]=useState(""),[output,setOutput]=useState(""),[ratings,setRatings]=useState<R[]>([]);
  const [anchors,setAnchors]=useState<R|null>(null);
  useEffect(()=>{let active=true;api('/protocol').then(v=>{if(active)setAnchors(v.optional_semantic_evaluation?.anchors || null);});return ()=>{active=false;};},[]);
  useEffect(()=>{setEnabled(false);setOutput("");},[jobId]);
  useEffect(()=>{let active=true;api(`/jobs/${jobId}/semantic-evaluations`).then(v=>{if(active)setRatings(v);});return ()=>{active=false;};},[jobId,p.revision]);
  const pair=pairs.find(r=>r.output_id===output);
  return <details><summary>Optional local AI-assisted semantic estimates (disabled by default)</summary>
    <p>This separate opt-in layer estimates genuine reflection, relevance, factual grounding, pedagogical usefulness, clarity and agency with anchored 1-4 ratings or null for insufficient evidence. Ratings require validation; they are not ground truth and never change script results. No inference runs until you explicitly press the assessment button.</p>
    <details><summary>Rating anchors (1 to 4; null means insufficient evidence)</summary><Json value={anchors}/></details>
    <label className="check"><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)}/>Enable optional local semantic assessment</label>
    {enabled && <><ModelSelect label="Optional semantic evaluator" models={p.modelState.models} value={model} onChange={setModel}/>
      <label>Output for semantic review<select value={output} onChange={e=>setOutput(e.target.value)}><option value="">Choose a completed output</option>{pairs.filter(r=>r.status!=="skipped").map(r=><option key={r.output_id} value={r.output_id}>{r.output_id} / {r.question}</option>)}</select></label>
      <p>Recorded defaults: temperature 0, seed 42, 1024 output tokens, context 4096, think false. Installed model/digest compatibility is checked before inference.</p>
      <button disabled={p.busy || !model || !pair} onClick={()=>{if(!pair)return;p.run(()=>api('/semantic-evaluations','POST',{enabled:true,model,output_id:pair.output_id,output_version:pair.output_version}),"Optional semantic estimate saved separately; inspect ratings or failure details.");}}>Run optional semantic assessment</button></>}
    <p>{ratings.filter(r=>r.status==="completed").length} completed AI-assisted estimates; {ratings.filter(r=>r.status!=="completed").length} failed attempts.</p>
    {ratings.map(r=><details key={r.id}><summary>{r.status} / {r.output_id} / {r.model} / {r.rubric_version}</summary><Json value={r}/></details>)}
  </details>;
}
