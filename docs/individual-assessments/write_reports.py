"""Render Markdown reports from actual recorded evidence; never invent results."""
import json
from pathlib import Path
from collections import Counter

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'evidence/manifest.json').read_text())
cases=json.loads((HERE/'evidence/results.json').read_text())
member_notes=json.loads((HERE/'member_notes.json').read_text())

# Risk scale: impact/likelihood Low=1, Medium=2, High=3. Product 1=Low,
# 2-3=Medium, 4-6=High, 9=Critical. Informational is reserved for observations
# without demonstrated adverse impact. Context can lower likelihood; no CVSS claim.
findings={
'PR-RESET':('Unauthenticated password reset permits controlled-account takeover','High','High','Critical','The unauthenticated forgot-password route returns a reset token. A requester who knows a registered email can use it to change that account’s password and log in. Critical reflects account compromise without a prior authenticated foothold when this demo behavior is exposed; no public deployment was tested.','backend/security/router.py: forgot_password and reset_password; backend/security/password_reset.py','Deliver reset capabilities exclusively to a verified email channel. Disable response tokens outside explicitly isolated development mode. Store a token digest, limit requests, and invalidate outstanding reset tokens/sessions after successful recovery.'),
'PR-ENUM':('Reset response distinguishes registered emails','Low','High','Medium','The registered response includes a non-null token; nonexistent emails return null despite identical message text. This reveals membership and supports targeted attacks. It is a supporting aspect of PR-RESET, not a separate takeover mechanism.','backend/security/router.py: forgot_password','Return the same public response shape regardless of account existence, never include a usable reset token, and limit automated probing.'),
'PR-SESSION':('Previously issued JWT survives password change','High','Medium','High','A controlled password change succeeds but the pre-change JWT still accesses the account. Exploitation requires a previously stolen token; it does not enable stealing a token on its own. Risk lasts until expiration.','backend/security/router.py: change_password; backend/security/jwt_manager.py; backend/security/authentication.py','Add a server-side token/session version or revoke sessions issued before password changes and recovery. Test the old token as well as a fresh login.'),
'PR-PII':('Synthetic identifiers are retained verbatim and included in prompt construction','Medium','Low','Medium','The real persistence function stores the fake email/phone query without redaction and the permitted admin view returns it. Prompt construction also retains it. Access is admin-restricted; unauthorized database access and actual provider transmission were not demonstrated. This is a data-minimization/privacy-design finding, not a legal compliance conclusion.','backend/agents/recommendation_agent/agent.py: record_search; backend/security/admin_router.py: get_user_detail; backend/llm/prompts.py','Minimize or redact identifiers before persistence and external model submission; offer a personalization opt-out, explicit purpose/access disclosure, retention/deletion policy, and least-privilege administrative access. Evaluate encryption against a defined storage threat model.'),
'PI-OUTPUT':('Hostile or malformed model responses bypass output validation','Medium','Low','Medium','Controlled response substitution demonstrates actual parser/coercion behavior and exceptions in analyze_query. Remote generation is mocked, but the application processing is real. These tests do not show that Gemini can be induced to return the fixture: likelihood is Low because this precursor remains unproven. Impact is incorrect intent/ranking or request failure, not command execution.','backend/agents/nlp_agent/agent.py: _parse_llm_json and analyze_query; backend/agents/nlp_agent/models.py','Validate the raw model object with strict types, permitted values, nonempty/bounded strings, flat bounded keyword lists and forbidden extra keys before use. Reject or explicitly fall back on malformed outputs. Test this separately from live attack resistance.'),
'PI-INJECTION':('Prompt manipulation changes analysis or output contract','Medium','Medium','High','The test evidence determines which attack criteria failed. An accepted manipulation can redirect dataset retrieval/ranking; model-format failures can degrade reliability. This finding does not demonstrate code execution or system-secret access. Single model samples do not estimate attack success rates.','backend/llm/prompts.py; backend/agents/nlp_agent/agent.py','Separate trusted instructions from untrusted request content, enforce allowlisted typed output values and keyword lists, validate intent consistency, and evaluate adversarial variants over repeated runs. Filtering alone is insufficient.'),
'PI-ROBUST':('Unexpected model response is not handled safely','Medium','Medium','High','A failed request indicates application robustness loss; use its recorded error/status to identify the exact cause before generalizing. No successful exploit beyond the recorded response is claimed.','backend/agents/nlp_agent/agent.py; backend/main.py','Validate model-returned types and catch malformed-response errors at the application boundary. Return structured client-safe errors or a declared fallback without hiding telemetry.'),
'RA-CLASSIFY':('Fallback classification does not consistently preserve requested intent','Medium','Medium','High','Specific prespecified relevance or intent checks fail under the recorded rule-based environment. Taxonomy limits and first-match precedence can cause incorrect task/domain selection. These results cover the small seed catalog, not all domains or Gemini.','backend/agents/nlp_agent/config.json; backend/agents/nlp_agent/agent.py','Prioritize specific phrases over generic triggers, handle unsupported intent explicitly, and evaluate task/domain accuracy against a reviewed diverse query set.'),
'RA-RELEVANCE':('Ambiguous or unsupported need can produce unrelated recommendations','Medium','Medium','High','Recorded seed-catalog cases show whether unsupported/ambiguous queries receive recommendations above the fixed threshold. A threshold score alone does not establish relevance or confidence. No invented dataset is claimed unless evidenced.','backend/agents/evaluation_agent/agent.py; backend/agents/evaluation_agent/scorer.py','Add uncertainty/clarification handling and calibrated abstention criteria. Evaluate false positives with independently reviewed relevance labels.'),
'RA-LANGUAGE':('Fallback language coverage differs for an equivalent translated request','Low','High','Medium','A paired English/Spanish example checks domain/task consistency. Failure demonstrates a narrow language-coverage limitation of the English model/taxonomy; it does not establish demographic discrimination or a language-wide statistical rate.','backend/agents/nlp_agent/preprocessing.py; backend/agents/nlp_agent/config.json','Declare supported languages before use, detect unsupported language, and either provide an explicit limitation or validated multilingual understanding. Expand matched-pair testing.'),
'RA-MODALITY':('Requested image modality is not enforced in recommendations','Medium','High','High','The image-request case checks understanding and returned tabular seed records. Catalog schemas have no data_type and evaluation scores no modality signal. A dataset may match domain/task while being unusable for the requested input type.','backend/agents/nlp_agent/config.json; backend/agents/discovery_agent/models.py; backend/agents/evaluation_agent/scorer.py','Add verified modality metadata, correct classification precedence, and require modality compatibility before recommending a dataset. Do not infer suitability from domain alone.'),
'RA-SOURCE':('Source-specific similarity transformations produce unequal scores for identical content','Low','Medium','Medium','Controlled candidates share content and metadata; real embeddings are scored using local transformed squared-L2 versus external cosine. A recorded difference demonstrates score comparability risk, not general preference for a particular source or protected-group bias.','backend/agents/discovery_agent/vector_store.py; backend/agents/discovery_agent/embeddings.py; backend/agents/evaluation_agent/scorer.py','Use a consistent normalized metric across sources, validate metadata inference, and calibrate ranking on cross-source relevance judgments before making fairness claims.'),
'RA-HARM':('Explicit discriminatory purpose is processed as ordinary discovery','Medium','Medium','High','The recorded request describes unfair exclusion and checks whether educational datasets are still recommended. Returned metadata is not an operational discrimination algorithm, but normalizing harmful purpose without safeguards is a misuse concern. No real protected-person data was used.','backend/main.py; backend/agents/nlp_agent/agent.py; backend/security/input_filter.py','Define misuse policy, evaluate intent-aware safeguards before retrieval, and provide safe responses for discriminatory requests. Measure false positives and refusals with reviewed cases.'),
}
roles=[('PR','gowsika-privacy-assessment.md','Gowsika','Privacy and Data Leakage Assessment','Authentication, authorization, JWT lifetime, password-reset capabilities, application-visible history handling, permitted admin access, synthetic PII persistence and prompt construction. No live PII transmitted; PR-04 substitutes an empty retrieval result only to isolate the real history/profile access logic.'),('PI','subasthican-prompt-assessment.md','Subasthican','Prompt Injection and Jailbreak Analysis','Fifteen adversarial requests through the real /nlp-agent route and application prompt with the configured Gemini model, plus fifteen explicitly controlled hostile/malformed model-response component tests. The latter run real spaCy/analyze_query while substituting remote generation; they do not establish live jailbreak success or resistance. Network requests use a 20-second timeout and one attempt. Provider errors are BLOCKED, not evidence of attack resistance. Only single samples per attack; no general attack-success rate is estimated.'),('RA','kageepan-responsible-ai-assessment.md','Kageepan','Responsible AI and Bias Assessment','Real rule-based spaCy query analysis, seeded catalog, transformer embeddings, FAISS retrieval, heuristic ranking and template explanations. Gemini and live Kaggle/OpenML/HuggingFace are deliberately excluded for reproducibility. RA-14 is a controlled synthetic-candidate component comparison using real embeddings; no protected-group population-level bias is measured.')]

for prefix,filename,name,special,scope in roles:
 selected=[c for c in cases if c['test_id'].startswith(prefix+'-')]
 counts=Counter(c['outcome'] for c in selected)
 present=sorted({f for c in selected for f in c['finding_ids'] if f in findings})
 text=f'''# {name} — Individual Vulnerability Assessment Draft

**Specialization proposed:** {special}. Lecturer allocation remains unconfirmed.

**Authorship and submission status:** AI-assisted execution and drafting for the team. This document does not claim that {name} independently performed these tests. The individual brief requires independent student work: review and reproduce the cases, verify evidence and ratings, write your own reflection, and comply with course rules for AI assistance before submission. This is an evidence-backed draft, not a certified completed individual submission.

## Current Fix Status

The findings below preserve the original baseline. Application fixes and subsequent retesting are documented separately in [fix verification](../fix-verification/README.md). All 69 fixed-application checks passed; these include application input guards and controlled model outputs, not live Gemini jailbreak verification. Latest credential checks confirmed Gemini key acceptance and three authenticated Kaggle results. The earlier full attempt recorded 12 passing browser flows and a duplicate failure. That duplicate is now fixed: 23 new unit tests, 38 authored ranking/abstention cases and 3 HTTP checks pass; live Gemini evaluation remains daily-quota blocked. See [current application fixes](../fix-verification/remaining-fixes.md). See [credential feedback](../fix-verification/evidence/live-integrations/credential-feedback.json). Student details and personal reflections are deferred by the user.

## Executive Summary

DATA NEBULA AI was assessed at commit `{manifest['tested_commit']}` on {manifest['run_date']}. This scope recorded {len(selected)} cases: **{counts['PASS']} PASS, {counts['FAIL']} FAIL, {counts['BLOCKED']} BLOCKED**. Passing means the selected criterion held in this observation; it does not establish general safety. Failed means the criterion did not hold; blocked means the required execution could not complete. {len(present)} supported finding categories are discussed below. No application source fixes were made during this assessment.

'''
 if present:text+='Major findings: '+ '; '.join(findings[f][0] for f in present)+'.\n\n'
 if counts['BLOCKED']: text+='**Baseline coverage limitation:** the 15 live prompt cases were rejected by the provider because the configured key was reported leaked. Controlled response tests assess only application output handling. Blocked cases do not satisfy evidence of completed model/security evaluation. Resolve their recorded environment/provider failure and rerun before claiming the 15-test requirement is fulfilled.\n\n'
 text+=f'''## Scope of Testing

{scope}

The production/local working database was not used for testing. Accounts and records were synthetic in a temporary SQLite database. HTTP route tests use FastAPI TestClient in-process, not a deployed browser session or external network ingress. TLS, reverse proxies, provider retention, cloud infrastructure, payments and legal/privacy compliance are not certified by this assessment. Screenshots were not captured; JSON request/response and component logs provide evidence.

All members must understand the full architecture: Next.js → FastAPI → NLP understanding → local/live retrieval → evaluation → ranked dataset metadata; signed-in history powers personalization. Internal agents are Python modules, not separate network services.

## Evaluation Methodology

1. Preserve baseline code and record its Git commit and database checksum.
2. Create synthetic test accounts and isolated storage; seed the real catalog/plans.
3. Execute defined scenarios with explicit expected behavior. Use real application routes or identified component calls; disclose test substitutions and deterministic configurations.
4. Record actual statuses, bodies, inputs, model traces or component outputs per test. Redact credentials and capabilities from saved evidence.
5. Compare observations with the stated criterion and map supported failures to findings.
6. Assess risk in the tested context; recommend mitigations without claiming they were implemented or validated.

Environment: Python `{manifest['python'].split()[0]}`, `{manifest['platform']}`. Exact installed package versions are in [requirements-lock.txt](evidence/requirements-lock.txt); transport/configuration and database checksums are in [manifest.json](evidence/manifest.json). Backend requirements are unpinned, so this installed environment may differ from previous developer runs. Gemini configured model: `{manifest['gemini_model']}`; credential configured: `{manifest['gemini_key_configured']}`. No credential values are published.

Risk rating: impact and likelihood each use Low=1, Medium=2, High=3. Product 1=Low, 2–3=Medium, 4–6=High, 9=Critical. Informational is reserved for non-adverse observations. This is a disclosed project matrix, not a formal CVSS score. Ratings are provisional and should be reviewed by the student using deployment context.

## Test Cases Performed

| ID | Objective | Outcome | Evidence |
|---|---|---|---|
'''
 for c in selected:text+=f"| {c['test_id']} | {c['objective']} | {c['outcome']} | [JSON log](evidence/{c['test_id']}.json) |\n"
 for c in selected:
  actual=json.dumps(c['actual_behavior'],indent=2,ensure_ascii=False)
  text+=f'''\n### {c['test_id']} — {c['objective']}

- **Objective:** {c['objective']}.
- **Input / scenario:** {c['input_scenario']}
- **Expected behavior:** {c['expected_behavior']}.
- **Actual behavior:**

```json
{actual}
```

- **Evidence:** [{c['test_id']}.json](evidence/{c['test_id']}.json), including request/model/component trace where available.
- **Observations:** {c['observations']}
- **Conclusion / outcome:** {c['outcome']}. {c['conclusion']}
- **Finding references:** {', '.join(c['finding_ids']) or 'No supported vulnerability assigned by this case.'}
'''
 text+='\n## Vulnerabilities Identified\n\n'
 if not present:text+='No vulnerability is established by the completed cases in this run. Any blocked model tests leave prompt resistance unresolved; do not interpret absence of findings as security.\n'
 for f in present:
  title,impact,likelihood,severity,explanation,location,mitigation=findings[f]
  refs=[c['test_id'] for c in selected if f in c['finding_ids']]
  links=', '.join(f'[{r}](evidence/{r}.json)' for r in refs)
  text+=f'''### {f} — {title}

- **Description and technical explanation:** {explanation}
- **Affected implementation:** `{location}`.
- **Evidence:** {links}.
- **Impact:** {impact}. See the scenario-specific effect described above.
- **Likelihood:** {likelihood}. Assessed in the context and prerequisites described above.
- **Severity / risk level:** {severity}, using the disclosed impact × likelihood matrix.
- **Mitigation:** {mitigation}

'''
 text+='## Risk Assessment\n\n| Finding | Impact | Likelihood | Risk level |\n|---|---|---|---|\n'
 if not present:text+='| No established finding | — | — | Unresolved where testing was blocked |\n'
 for f in present:
  title,impact,likelihood,severity,*_=findings[f];text+=f'| {f}: {title} | {impact} | {likelihood} | {severity} |\n'
 text+='\n## Mitigation Strategies\n\n'
 for f in present:text+=f"- **{f}:** {findings[f][-1]}\n"
 if not present:text+='Resolve the blocked tests first. General defensive recommendations should not be presented as mitigations for demonstrated vulnerabilities without evidence.\n'
 text+='\nRetest each adopted change at a new commit using the same baseline input and record new evidence separately. Do not overwrite baseline observations with assumed fixed outcomes.\n'
 text+='\n## Reflection\n\n'+member_notes[prefix]['reflection']+'\n'
 text+='\n## Individual Viva Preparation\n\nThese are evidence-grounded study answers. Independently verify the cases before presenting them as your own work. Viva attendance and performance cannot be completed by this document.\n'
 for question,answer in member_notes[prefix]['viva']:
  text+='\n### '+question+'\n\n'+answer+'\n'
 text+='''
## References

- [Individual Assignment Brief](../Individual%20Assignment%20Brief.pdf): specialization, minimum tests, evidence, report sections and viva criteria.
- [Group Assignment Brief](../Group%20Assignment%20Brief.pdf): system scope and group deliverables.
- Local application code and recorded case logs referenced above. No external standard compliance is claimed.

## Remaining Submission Work

- [ ] Confirm specialization and student ID with lecturer/member.
- [ ] Independently reproduce and validate cases; complete blocked live cases using a valid local key.
- [ ] Review conclusions/ratings and adapt the evidence-based reflection using your own experience.
- [ ] Apply any required institutional report template and finalize authorship under course AI-assistance rules.
- [ ] Attend and defend the individual viva.
'''
 (HERE/filename).write_text(text)

summary='''# Individual Assessments — Evidence and Draft Reports

These are AI-assisted assessments of the existing baseline, not claims of independent student completion. Lecturer specialization allocation remains pending. Each student must reproduce their tests, review the findings, author their own reflection/report, and follow course rules for AI assistance. Subasthican’s 30 entries comprise 15 blocked live prompt attempts plus 15 completed controlled output-boundary tests; these are explicitly different execution modes. Original baseline evidence is preserved here. Implemented fixes and 69 passing retests are documented in [fix verification](../fix-verification/README.md).

| Member | Proposed scope | PASS | FAIL | BLOCKED | Report |
|---|---|---|---|---|---|
'''
for prefix,filename,name,special,scope in roles:
 c=Counter(x['outcome'] for x in cases if x['test_id'].startswith(prefix+'-'))
 summary+=f'| {name} | {special} | {c["PASS"]} | {c["FAIL"]} | {c["BLOCKED"]} | [Draft]({filename}) |\n'
summary+='''
A FAIL is a documented failed criterion, not an unfinished execution. A BLOCKED case is incomplete evaluation. A PASS applies only to the tested criterion/configuration. JSON logs are the evidence; no UI screenshots are claimed. Drafts contain all eight report sections, scenario-level actual results, findings/risk matrix and recommendations; personal reflection and student validation remain pending.

## Reproduce

From the repository root, create an isolated Python environment and install `backend/requirements.txt` plus `httpx`, then install the `en_core_web_sm` spaCy model. This run recovered dependencies from cache; Kaggle was not installed because it is lazy-loaded and no live external-source cases were run. All dependencies actually used passed `pip check`. Configure the project’s existing `.env` Gemini key/model for live prompt cases. Never publish that file.

```bash
python docs/fix-verification/run_retests.py
python docs/individual-assessments/write_reports.py
```

The runner sets a temporary database and random test-only JWT secret before importing the backend. It uses controlled accounts, invokes actual routes/components, writes redacted JSON evidence, checks the original database checksum, and deletes test storage at completion. Baseline runners refuse to overwrite the archived evidence. The fix runner writes separate verification logs. Only test data is sent in live prompt calls. Responsible AI cases use local seeded catalog and forced rule-based understanding; privacy PII test does not send its fake identifiers externally.

Recorded environment and exact package versions: [manifest](evidence/manifest.json), [dependency snapshot](evidence/requirements-lock.txt). Full case data: [results](evidence/results.json). Each report links to individual JSON files.
'''
(HERE/'README.md').write_text(summary)
print('Wrote three evidence-backed Markdown report drafts and summary.')
