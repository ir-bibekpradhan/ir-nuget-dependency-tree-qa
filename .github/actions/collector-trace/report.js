const fs = require('fs');
const path = require('path');
const trace = path.join(process.env.QA_SCENARIO_PATH || '', '.qa', 'invocations.jsonl');
if (fs.existsSync(trace)) {
  const invocations = fs.readFileSync(trace, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const result = {packageListInvocations: invocations.length, referenceProbeInvocations: 1,
                  additionalCollectorInvocations: Math.max(0, invocations.length - 1)};
  console.log('IR_QA_LIST_FALLBACK_TRACE ' + JSON.stringify(result));
  if (process.env.GITHUB_STEP_SUMMARY) {
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,
      '\nPost-cleanup package-list replay trace: ' + JSON.stringify(result) + '\n');
  }
}
