import { test, expect } from '@playwright/test';

test('v2/v3 comparison, filters, evidence and semantic opt-in without inference',async({page,request})=>{
  const token=Date.now();
  const post=async(path:string,data:any)=>{const r=await request.post('/api/'+path,{data});expect(r.ok(),await r.text()).toBe(true);return r.json();};
  const dataset=await post('datasets',{name:'V3 regression '+token});
  const scenario=await post('scenarios',{dataset_id:dataset.id,row:{inputs:{learning_goal:'Learn Python',planned_activity:'Write Python functions',reported_time:{value:35,unit:'minutes'},planned_time:{value:20,unit:'minutes'}}}});
  await post(`scenarios/${scenario.id}/review`,{decision:'approved',reviewer:'browser-test',feedback:'Synthetic browser fixture'});
  const bank=await post('banks',{name:'V3 test bank '+token});
  const question=await post('questions',{bank_id:bank.id,text:'Which Python approach would you try next?'});
  await post(`questions/${question.id}/review`,{decision:'approved',reviewer:'browser-test',feedback:'Synthetic browser fixture'});
  const ds=await post('snapshots',{kind:'dataset',dataset_id:dataset.id,name:'V3 test dataset '+token});
  const bs=await post('snapshots',{kind:'bank',bank_id:bank.id,name:'V3 test bank '+token});
  const job=await post('experiments',{name:'V3 experiment '+token,dataset_snapshot_id:ds.id,bank_snapshot_id:bs.id,methods:['fixed']});
  await expect.poll(async()=> (await (await request.get('/api/jobs/'+job.id)).json()).status).toBe('completed');
  const report=await post(`jobs/${job.id}/script-evaluation`,{});
  const legacyCriteria={usefulness:{pass:1,flag:0,inconclusive:0,evaluated:1,decision_coverage:1}};
  const old={...report,operational:undefined,id:'V2-UI-FIXTURE',version:'fixed-rubric-v2-method-blind',created_at:'2020-01-01',criteria:legacyCriteria,
    by_condition:report.by_condition.map((g:any)=>({...g,criteria:legacyCriteria,matched_cases:{...g.matched_cases,criteria:legacyCriteria}})),
    pairs:report.pairs.map((r:any)=>({...r,criteria:legacyCriteria}))};
  // Historical display fixture only; never presented as actual model execution.
  await page.route(`**/api/jobs/${job.id}/metrics`,async route=>{
    const response=await route.fetch();const data=await response.json();
    data.script_evaluation.reports=[old,report];
    await route.fulfill({json:data});
  });
  let semanticRequests=0;
  page.on('request',r=>{if(r.url().endsWith('/api/semantic-evaluations') && r.method()==='POST')semanticRequests++;});
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await page.getByRole('button',{name:'Evaluation',exact:true}).click();
  await page.getByRole('combobox',{name:'Experiment to evaluate',exact:true}).selectOption(job.id);
  await expect(page.getByText('1/1 questions evaluated by scripts',{exact:true})).toBeVisible();
  await page.getByRole('combobox',{name:'Compare saved report',exact:true}).selectOption(old.id);
  await expect(page.getByText('Legacy wording cues',{exact:true})).toBeVisible();
  await page.getByRole('combobox',{name:'Evaluation version',exact:true}).selectOption(old.id);
  await expect(page.getByText('Legacy wording cues',{exact:true}).first()).toBeVisible();
  await page.getByRole('combobox',{name:'Evaluation version',exact:true}).selectOption(report.id);
  await page.getByRole('combobox',{name:'Compare saved report',exact:true}).selectOption(old.id);
  await page.getByRole('combobox',{name:'Method filter',exact:true}).selectOption('fixed');
  await page.getByRole('combobox',{name:'Criterion filter',exact:true}).selectOption('factual_grounding');
  await page.getByRole('combobox',{name:'Status filter',exact:true}).selectOption('inconclusive');
  await expect(page.getByText('1 matching outputs.',{exact:false})).toBeVisible();
  const pair=page.locator('details').filter({has:page.locator('summary',{hasText:/inconclusive \/ fixed/})}).first();
  await pair.locator('summary').first().click();
  await expect(pair.getByText('Learn Python',{exact:true})).toBeVisible();
  await expect(pair.locator('pre').filter({hasText:'metric_version'}).first()).toContainText('metric_version');
  await page.getByText('Optional local AI-assisted semantic estimates (disabled by default)',{exact:true}).click();
  await expect(page.getByRole('checkbox',{name:'Enable optional local semantic assessment',exact:true})).not.toBeChecked();
  await expect(page.getByRole('button',{name:'Run optional semantic assessment',exact:true})).toHaveCount(0);
  expect(semanticRequests).toBe(0);expect(errors).toEqual([]);
});
