# Compatibility and verification

Date: 2026-11-04. The same portable Skill uses a pinned Python engine. Model access
is supplied by the user's host; these examples do not buy or call model APIs.

| Environment | Integration supplied | Verification in this release |
|---|---|---|
| Local Python 3.9+ | Complete offline Skill, CLI, wheel | Local runtime tests; see VALIDATION.md |
| Local stdio MCP host | Seven read-only tools | Real subprocess protocol replay; no model involved |
| Claude Code | Research-only marketplace/plugin manifest | Manifest/paths inspected; app/model session not tested |
| ChatGPT desktop / Codex | Portable Skill folder; copy/install to documented directory | Bundle copied and executed from isolated path; app/model auto-invocation not tested |
| Kimi Code | Same Skill without Claude path variables | Portable bundle execution; app/model session not tested |
| DeepSeek API application | Function schema + local Python dispatcher | Local dispatcher parity only; no paid API run |
| Grok API application | Same function schema + local Python dispatcher | Local dispatcher parity only; no hosted MCP endpoint |
| Text-only chat | Prompt, supplied evidence and local reports | No claim of script execution in chat |

Official host docs, reviewed 2026-11-04:
- https://learn.chatgpt.com/docs/build-skills
- https://developers.openai.com/plugins
- https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html
- https://api-docs.deepseek.com/guides/tool_calls/
- https://docs.x.ai/developers/tools/remote-mcp

Documented support is not proof of installation or execution in a particular
account. Runtime capabilities, permissions and model behavior vary. Do not label
a simulated provider request as an actual model test. No provider compatibility
badge implies endorsement. Remote hosting and marketplace submission are outside
this release; local MCP needs an execution-capable host.
