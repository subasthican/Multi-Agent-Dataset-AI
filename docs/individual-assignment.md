# Individual Assignment — AI Security Audit & Vulnerability Assessment

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

> **Open question:** the brief defines 4 specializations ("Student 1–4"), but
> `docs/members.md` currently has 3 confirmed members (you, Gowsika, Kageepan).
> Either there's a 4th group member not yet reflected in this repo's docs, or
> only 3 of these 4 specializations apply to your group — confirm with your
> lecturer/team which specialization **you specifically** were assigned, since
> that determines which system component you test and write about.

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

## How this maps onto the actual system in this repo

Once you confirm your specialization, here's roughly where to point your testing
(happy to help design and run the actual test cases once this is confirmed):

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
  config, rate limiting (none implemented).

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
