import { chromium } from '@playwright/test';
const browser = await chromium.launch({channel:'msedge', headless:true});
try {
  const page = await browser.newPage({viewport:{width:1600,height:1100}});
  page.setDefaultTimeout(15000);
  const failures=[];
  page.on('pageerror', error => {failures.push(error.message); console.log('PAGE ERROR',error.message);});
  await page.goto('http://127.0.0.1:8000');
  await page.getByRole('button',{name:'Metrics',exact:true}).click();
  await page.getByRole('combobox',{name:'Experiment',exact:true}).selectOption('job_ded5a2d2cb8d49ff');
  await page.getByText('90/90 questions evaluated by scripts',{exact:true}).waitFor().catch(async error => {console.log((await page.locator('body').innerText()).slice(0,5000)); throw error;});
  await page.getByRole('heading',{name:'Compare Fixed bank, RAG and LLM'}).waitFor();
  if (await page.locator('tbody tr').count() !== 3) throw new Error('Expected three comparison rows');
  await page.screenshot({path:'../docs/browser-script-metrics-3010.png',fullPage:true});
  if (failures.length) throw new Error(failures.join('\n'));
  console.log('Live 3010: 90 evaluated questions, three method rows, no browser errors.');
} finally { await browser.close(); }
