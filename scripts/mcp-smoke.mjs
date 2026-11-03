import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import {resolve} from 'node:path';
import {readFileSync} from 'node:fs';
const require=createRequire(resolve(process.env.MCP_SDK_ROOT || '.', 'package.json'));
const {Client}=await import(require.resolve('@modelcontextprotocol/sdk/client/index.js'));
const {StdioClientTransport}=await import(require.resolve('@modelcontextprotocol/sdk/client/stdio.js'));
const client=new Client({name:'ahasignals-research-validation',version:'0.1.0'});
try {
 await client.connect(new StdioClientTransport({command:'python3',args:[resolve('earnings-review/scripts/analysis_review.py'),'mcp'],stderr:'pipe'}));
 const {tools}=await client.listTools();assert.equal(tools.length,7);assert.ok(tools.every(t=>t.annotations.readOnlyHint));
 for (const [name,status] of [['correct','SUPPORTED'],['wrong','CORRECTION_REQUIRED'],['insufficient','UNKNOWN']]) {
   const packet=JSON.parse(readFileSync(`earnings-review/examples/analysis/${name}.json`));
   const reply=await client.callTool({name:'review_analysis_claims',arguments:{packet}});
   assert.equal(reply.isError,false);const result=JSON.parse(reply.content[0].text);
   assert.equal(result.claims[0].numericReview.status,status);assert.equal(result.analysisStatus,'NOT_FULLY_VERIFIED');
 }
 const packet=JSON.parse(readFileSync('earnings-review/examples/analysis/correct.json'));
 const bad=await client.callTool({name:'review_analysis_claims',arguments:{packet,sourceText:'tampered'}});
 assert.equal(JSON.parse(bad.content[0].text).claims[0].numericReview.evidenceLevel,'SOURCE_BINDING_FAILED');
 console.log('Official MCP SDK: seven tools; three outcomes; tampered-source rejection. No model calls.');
} finally { await client.close(); }
