import { useState } from "react";
import type { Common } from "../types";
import { ScriptEvaluation } from "./ScriptEvaluation";

export function Metrics(p: Common) {
  const [jobId, setJobId] = useState("");
  return <>
    <label>Experiment<select value={jobId} onChange={e => setJobId(e.target.value)}>
      <option value="">Select experiment</option>
      {p.jobs.filter(j => j.kind === "experiment").map(j => <option key={j.id} value={j.id}>{j.name} / {j.id}</option>)}
    </select></label>
    <ScriptEvaluation jobId={jobId} p={p} />
    <p>Historical human and AI labels remain in exports. The results shown here come exclusively from fixed metric scripts.</p>
  </>;
}
