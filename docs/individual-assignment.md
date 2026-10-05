# Individual Assignment — AI Security Audit & Vulnerability Assessment
## Verified application fixes — 5 October 2026

The original assessment findings are retained as baseline evidence. The fixes were implemented at the user's request and **all 69 application retests passed**, with a separate passing, idempotent migration check. See [fix verification](fix-verification/README.md) for outcomes, evidence and limitations.

- **Subasthican:** input guards, untrusted-input prompt framing, strict model-output schema and safe fallback. Fifteen original attack inputs are rejected before provider invocation; fifteen controlled malformed outputs are handled safely. Latest Gemini key is accepted, but live resistance remains unverified due to quota/high-demand responses; authenticated Kaggle returned three datasets.
- **Gowsika:** private reset-email flow, reset-token digests and single-use handling, password-change/recovery session invalidation, contact redaction, independent atomic usage counters, quotas on standalone routes HTTP(S) catalog URL validation, transactional admin audit logs and password confirmation with failed-attempt throttling for deletions, plus authenticated encryption and migration of stored search text. SMTP configuration is deferred by the user; tests mock delivery.
- **Kageepan:** specific intent precedence, language/unsupported-domain warnings, modality metadata and filtering, consistent normalized similarity, discriminatory-request guards, clearer heuristic score/privacy disclosures and frontend recovery/session updates.

Student IDs, lecturer-confirmed specializations and each member's own reflection are deferred as requested. Draft notes and viva practice material are provided; they do not certify independent student work or a completed viva. These finite checks do not establish 100% system security or assessment completion.


Source: `Individual Assignment Brief.pdf` (IT3041 – Information Retrieval and Web
Analytics). **This is separate from, and in addition to, the group assignment** —
same course, same groups, but graded and submitted individually. 100 marks total,
independent of the group's 100 marks.

## What it is

Each student independently red-teams **the actual Agentic AI system the group
built** (this repo) from one assigned angle, then writes a formal vulnerability
assessment report and defends it in an individual viva. The brief is explicit:
*"The objective is not to redesign or improve the existing system, but to
critically assess its robustness."* You're acting as an AI Security Analyst /
Red Team member testing your own team's system — not writing new features.

## Specializations (lecturer-assigned, one per student)

| # | Specialization | Evaluation areas | Expected outcome |
|---|---|---|---|
| 1 | Prompt Injection & Jailbreak Analysis | Prompt injection, jailbreaks, prompt leakage, instruction override, prompt manipulation, prompt robustness | Vulnerability assessment of prompt-related weaknesses + countermeasures |
| 2 | Privacy & Data Leakage Assessment | Sensitive info leakage, PII exposure, conversation memory leakage, authentication weaknesses, user data protection, privacy compliance | Privacy and data protection assessment |
| 3 | Responsible AI & Bias Assessment | Hallucinations, bias, toxic responses, fairness, transparency, explainability, harmful content generation | Responsible AI compliance and vulnerability assessment |
| 4 | Information Retrieval & Security Assessment | Retrieval accuracy, retrieval manipulation, hallucination due to retrieval, source reliability, authentication, authorization, API security, communication protocol security | Technical security assessment of the IR pipeline |

### Proposed mapping (pending lecturer/team confirmation)

The brief defines 4 specializations, but `docs/members.md` has 3 confirmed
members. Mapping proposed here follows who actually built and understands each
part of the system — swap freely once the lecturer assigns for real, or if
there's a 4th member not yet reflected in this repo:

| Member | Specialization | Why |
|---|---|---|
| **Member 1 (you)** | Prompt Injection & Jailbreak Analysis | You built the NLP Agent and the Gemini prompt/LLM integration (`backend/agents/nlp_agent/`, `backend/llm/`) — you know exactly what the prompt does and doesn't guard against. |
| **Member 2 (Gowsika)** | Privacy & Data Leakage Assessment | She owns the auth system (`backend/security/`) — JWT, password hashing, the reset-token flow — the exact surface this specialization tests. |
| **Member 3 (Kageepan)** | Responsible AI & Bias Assessment | Closest fit to the frontend's transparency/explanation UI (`ExplanationCard`) and the system's Responsible AI story generally, given Information Retrieval & Security overlaps heavily with Member 1's Discovery/Kaggle work. |
| *(unassigned)* | Information Retrieval & Security Assessment | No 4th member confirmed yet. If your group is actually 4 people, this is the natural specialization for whoever isn't listed in `docs/members.md` yet — the lecturer must determine how this specialization applies to a three-person group; do not assume a fourth member or double assignment is required. |

This is my proposal based on system ownership, not a lecturer assignment —
confirm the real assignment before committing significant testing time to it.

## Per-member individual work plans

These existing member files now cover both the group agent responsibility and the proposed individual audit:

| Member | Group responsibility | Proposed individual specialization | Work plan |
|---|---|---|---|
| Subasthican | NLP + orchestration | Prompt Injection and Jailbreak Analysis | [Member plan](subasthican-nlp-agent.md#individual-assignment--subasthican) |
| Gowsika | Discovery + security | Privacy and Data Leakage Assessment | [Member plan](gowsika-discovery-agent.md#individual-assignment--gowsika) |
| Kageepan | Evaluation + frontend | Responsible AI and Bias Assessment | [Member plan](kageepan-evaluation-agent.md#individual-assignment--kageepan) |

Each contains 15 proposed tests, expected behavior, an evidence template, and a report checklist. **AI-assisted execution is now recorded:** Gowsika’s 15 privacy cases and Kageepan’s 15 local Responsible AI cases completed; Subasthican’s 15 live prompt cases are blocked by Google rejecting the key as reported leaked. Fifteen additional controlled model-output boundary tests completed, separately labeled. See [results and report drafts](individual-assessments/README.md). These are not claims of independent student completion. The lecturer's specialization allocation remains pending. Each member must independently perform and document their assigned testing and author their own report.

## Testing requirements

- **Minimum 15 independent test cases** in your assigned specialization.
- Each test case documented with: Test Objective, Input/Attack Scenario,
  Expected Behaviour, Actual Behaviour, Evidence (screenshots/logs),
  Observations, Conclusion.
- Every vulnerability found gets a severity: **Critical / High / Medium / Low /
  Informational**, with technical justification for the rating.

## Report structure (80 marks)

1. Executive Summary
2. Scope of Testing (system evaluated, specialization, components in scope, limitations)
3. Evaluation Methodology (testing approach, tools, environment, criteria)
4. Test Cases Performed (Test ID, Objective, Input, Expected/Actual Result, Evidence, Outcome — all 15+)
5. Vulnerabilities Identified (Description, Evidence, Impact, Likelihood, Severity, Risk Level, Technical Explanation)
6. Risk Assessment — a risk matrix summarizing all findings (Vulnerability × Impact × Likelihood × Risk Level)
7. Mitigation Strategies (practical fix per vulnerability)
8. Reflection (challenges, lessons learned, recommendations)

**Report rubric (80 marks):**

| Criterion | Marks |
|---|---|
| Testing Methodology and Coverage | 20 |
| Quality of Vulnerability Analysis | 25 |
| Risk Assessment and Severity Classification | 15 |
| Mitigation Strategies | 10 |
| Report Quality, Evidence, and Technical Writing | 10 |
| **Total** | **80** |

## Individual Viva (20 marks)

Be ready to explain: testing methodology, rationale for chosen test cases, why
attacks succeeded or failed, technical reasoning behind each vulnerability,
justification of assigned risk levels, proposed mitigations, and Responsible AI
implications.

## Baseline testing map (before the verified fixes)

The following records the original baseline testing targets. Current status is summarized above and in the fix-verification report:

- **Prompt Injection/Jailbreak** → `backend/agents/nlp_agent/` (the Gemini call
  in `llm/gemini_client.py` + `llm/prompts.py`) — there's currently **no input
  sanitization** in front of the LLM prompt (that was scoped to Member 2's
  `backend/security/input_filter.py`, still a TODO). This is a real, honestly-disclosed
  gap, not a hidden one — worth testing.
- **Privacy/Data Leakage** → the new auth system (`backend/security/`): password
  storage (bcrypt-hashed, verify it's never logged/returned), JWT handling, the
  `forgot-password` dev-mode reset token (it's returned directly in the API
  response since no email provider is wired up — that's a deliberate, documented
  simplification, but worth analyzing as a real exposure in a red-team report).
- **Responsible AI/Bias** → `backend/agents/evaluation_agent/` explanations and
  `backend/agents/nlp_agent/` domain/task classification (rule-based fallback
  uses fixed keyword lists in `config.json` — could systematically misclassify
  underrepresented phrasings/domains).
- **IR/Security** → `backend/agents/discovery_agent/` (FAISS search),
  `backend/agents/dataset_collection_agent/` (live Kaggle calls), and the API
  layer generally — e.g. no auth currently required on `/discover` itself, CORS
  config, daily quotas on `/discover`, and unmetered standalone agent endpoints. Signed-in quotas currently depend on deletable search-history rows.

## Related: Group Mid Evaluation Marking Rubric (20 marks, Week 6)

Transcribed from `docs/marking schema for viva/IMG_6461–6467` (IT3041 – Mid
Evaluation Marking Rubric, 4-page PDF). This is the **group** mid-evaluation
rubric, not the individual one above — kept here since it was photographed
alongside it.

| # | Criterion | Excellent | Good | Satisfactory | Limited/Poor | Marks |
|---|---|---|---|---|---|---|
| 1 | Why This Domain Was Selected | Strongly justifies the selected domain based on a meaningful real-world problem, its importance, target users, and suitability for an Agentic AI solution | Clear justification with good understanding, but lacks some depth | Basic justification is provided, but the importance or suitability of the domain is weakly explained | Cannot clearly justify the domain or identify the problem being addressed | 3 |
| 2 | Understanding of the Proposed System | Clearly explains what the system is, the problem it solves, target users, expected functionality, and value of the proposed solution | Good understanding with minor gaps in explanation | General understanding, but some important aspects of the system are unclear | Cannot clearly explain what the system does or why it is needed | 4 |
| 3 | Agents and Their Roles | Clearly identifies the agents, explains why each agent is required, what each agent does, how agents interact, and how they collectively achieve the system objective | Agents and major responsibilities are clearly explained with minor gaps in interactions or justification | Agents are identified, but their responsibilities or interactions are only basically explained | Agents are poorly defined or students cannot explain their purpose and interactions | 4 |
| 4 | Implementation Plan | Presents a clear and realistic development plan and demonstrates strong understanding of how LLM, NLP, IR, security, agent communication, and other required components will eventually work together | Good implementation plan covering most important components | Basic plan exists, but several technical components or development stages are unclear | Plan is unrealistic/incomplete or students cannot explain how the proposed system could be developed | 3 |
| 5 | Responsible AI Plan | Clearly identifies relevant Responsible AI issues for the proposed system and provides realistic plans for addressing fairness, transparency, explainability, privacy, security, potential misuse, and other domain-specific risks | Identifies major Responsible AI concerns and provides reasonable approaches to address most of them | Demonstrates basic awareness of Responsible AI, but proposed approaches are generic or incomplete | Little understanding of Responsible AI risks or cannot explain how they will be addressed | 3 |
| 6 | Commercialization Plan | Clearly identifies target users/market, value proposition, potential pricing/revenue model, deployment approach, and convincingly explains why users or organizations would adopt/pay for the system | Provides a reasonable commercialization concept covering most major areas | Basic commercialization idea exists but lacks clear market, pricing, deployment, or business justification | Commercialization concept is unclear, unrealistic, or students cannot explain who would use/pay for the solution | 3 |
| | | | | | **Total** | **20** |
