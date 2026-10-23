# Evaluation Results — Personal Opportunity Radar

## Overview

We conducted an initial evaluation of Personal Opportunity Radar across three areas:

1. CV-related question answering (QA)
2. Job recommendation relevance
3. Evidence quality of generated job explanations

The results below are preliminary. The evaluation uses a small sample and manually assigned labels, so the findings should be interpreted as exploratory rather than as a definitive measure of overall system performance.

## 1. CV Question Answering

Ten CV-related questions were evaluated using a manual correctness score from 0 to 2 and claim-level support labels.

| Metric | Result |
|---|---:|
| Number of questions | 10 |
| Sum of correctness scores | 11 |
| Average correctness score | 1.1 / 2 |
| Normalized correctness score | 55% |
| Supported factual claims | 89 / 102 |
| Claim-level faithfulness | 87.25% |
| Answers containing at least one unsupported claim | 7 / 10 |
| Answer-level unsupported-claim rate | 70% |

### Findings

The average correctness score was 1.1 out of 2 (55% when normalized). At the claim level, 89 of 102 factual claims were labelled as supported by the available CV evidence, giving a preliminary faithfulness score of 87.25%.

However, 7 of the 10 answers contained at least one unsupported claim. This answer-level rate does not contradict the claim-level faithfulness score: an answer can contain several supported claims and still include one unsupported claim.

Examples identified during the manual review included attributing the RAG project to the Research Assistant role when the CV lists it as a separate project, mentioning a Toyota thesis that was not established by the CV evidence, and adding technology or experience claims not supported by the CV.

**Interpretation:** The system often produced claims that were supported by the CV, but unsupported details appeared in a substantial proportion of answers. The labels and claim counts were entered manually and should be verified before these figures are treated as final.

## 2. Job Recommendation Relevance

Five recommended jobs were assessed manually on a 0–2 relevance scale:

- **2:** High potential relevance
- **1:** Partial relevance, with notable gaps
- **0:** Low overall suitability or a major requirement mismatch

| Job | System score | Human relevance score (0–2) | Main observation |
|---|---:|---:|---|
| Master's Thesis: AI in Integrated Logistics Support — AFRY AB | 1.06 | 2 | Relevant to the candidate's AI background and Master's studies; ILS experience was not established. |
| AI Product Associate — Legora AB | 0.42 | 0 | AI-related skills overlap, but the stated legal qualification and legal-work requirements are major gaps. |
| AI Product Engineer — A Hub AB | 1.31 | 2 | Strong overlap with LLM, RAG, and Python experience; some agent, modern web-stack, and product-ownership requirements were not evidenced. |
| AI Adoption and Governance Lead — Etraveli Group AB | 1.60 | 1 | Some AI and LLM overlap, but enterprise adoption, governance, and rollout experience were not established. |
| AI Developer — Sveaviken PM AB | 1.74 | 1 | AI skills overlap, but the role requires fluent Swedish and the CV lists Swedish as beginner; some web-stack skills were also not established. |

### Aggregate results

| Metric | Result |
|---|---:|
| Number of jobs assessed | 5 |
| Sum of human relevance scores | 6 / 10 |
| Average human relevance score | 1.2 / 2 |
| Normalized human relevance score | 60% |
| Spearman rank correlation between system score and human score | 0.1054 |
| Spearman correlation p-value | 0.8660 |
| Kendall's tau | 0.0000 |
| Kendall's tau p-value | 1.0000 |

The correlation analysis found only a very weak positive Spearman association between the system scores and the preliminary human relevance scores (rho = 0.1054). With only five jobs and manually assigned human scores, this result is highly uncertain and should not be interpreted as strong evidence for or against the ranking method. The correlation statistics are exploratory.

The system scores shown above are the positive values displayed in the application. They should not be interpreted as probabilities or percentages.

## 3. Generated Job Explanation Review

One generated explanation covering four jobs (Legora, A Hub, Etraveli, and Sveaviken) was reviewed at the claim level. Nineteen claims were recorded and assigned qualitative labels, according to the uploaded summary. The earlier draft said 18; this count should be reconciled with the CSV before final submission.

### Findings

- Some claims about the candidate's Python, LLM-related projects, RAG work, dialect standardization, and sentiment-classification experience were supported by the available CV information.
- Some claims, including prompt engineering, AI-agent or automation experience, and workflow ownership, were not directly established by the available CV evidence or were only partially supported.
- The explanation described A Hub and Sveaviken as strong fits, but it did not clearly surface the important mismatch between Sveaviken's fluent-Swedish requirement and the candidate's beginner Swedish level.
- The review used mixed qualitative labels (for example, supported, partially supported, unverified, and inference). Because the labels were not consolidated into one consistent scoring scheme, no overall explanation-faithfulness percentage is reported.

**Interpretation:** The explanations included useful evidence-based matching, but some claims were stronger than the CV evidence justified, and an important job requirement was omitted from the discussion.

## 4. Overall Findings

Across the three evaluation areas, the initial results suggest that:

1. **CV QA:** Claim-level support was relatively high (87.25%), but 70% of answers contained at least one unsupported claim. This highlights the need to evaluate both individual claims and whole answers.
2. **Job recommendations:** The five-job sample showed mixed human relevance scores. Some technically relevant roles also had major eligibility or experience gaps. The small sample does not support a reliable general conclusion about ranking quality.
3. **Generated explanations:** Explanations sometimes connected jobs to relevant projects and skills, but also included partially supported or unverified statements and did not always highlight critical requirements.

## 5. Limitations and Next Steps

- The evaluation sample is small: 10 CV questions, five jobs, and one generated explanation covering four jobs (with 19 explanation claims listed in the latest summary).
- Human relevance and correctness labels were manually assigned and are preliminary.
- The explanation review used mixed qualitative labels, so a single aggregate faithfulness score cannot yet be reported.
- The correlation statistics based on five jobs are exploratory and should not be treated as a robust ranking-performance estimate.
- Before final reporting, verify each CV QA correctness label, factual-claim count, and support label against the CV; independently review the five job relevance scores; and apply a consistent claim-labeling rubric to future explanation evaluations.

## Conclusion

The initial evaluation shows promising evidence that Personal Opportunity Radar can identify relevant skills and projects, but it also reveals risks from unsupported CV claims and incomplete discussion of job requirements. Further evaluation with more questions, a larger and more diverse job set, and consistently applied human labels is needed before drawing firm conclusions about system quality.


## 6. Progress Update: Review of Existing Evaluation Files

The uploaded evaluation summaries were reviewed to identify what can be reported now and what still needs verification. This section records the current status; it does not change any manually assigned scores.

### CV QA review status

The uploaded CV QA summary reports 10 questions, a correctness score sum of 11/20, an average correctness score of 1.1/2 (55%), 89 supported claims out of 102 factual claims (87.25%), and 7 answers containing at least one unsupported claim (70%). The summary explicitly states that these metrics are based on manually entered labels and are not final until the labels and claim counts have been checked against the CV.

The following items were flagged for a closer review based on the current scoring notes:

- **QA04 — Research experience:** Check that the Research Assistant role is not incorrectly credited with the separate RAG project.
- **QA05 — AI/ML projects:** Check the unsupported reference to a Toyota thesis against the original answer and CV.
- **QA06 — Academic qualifications:** Check whether claims about coursework or foundational knowledge are actually supported by the CV.
- **QA09 — Technology mentioned in the CV:** Re-read the question and answer together to confirm whether the score reflects what the question asks and what the CV says.

These are review flags, not confirmed scoring corrections. The original CV and the full question-answer text must be checked before changing scores or claim counts.

### Job recommendation review status

The uploaded job summary reports five jobs with human relevance scores of 0, 1, or 2: one job scored 0, two scored 1, and two scored 2. The score sum is 6/10, giving an average of 1.2/2 (60%). These are preliminary manual judgments, not validated ground truth.

The uploaded comparison summary reports Spearman rho = 0.1054 (p = 0.8660) and Kendall's tau = 0.0000 (p = 1.0000). Because only five jobs were assessed and the human labels are preliminary, these statistics are exploratory and should not be presented as robust evidence of ranking performance. The raw CrossEncoder scores are relevance scores, not probabilities.

### Generated explanation review status

The latest uploaded explanation summary lists **19 claims**. Its qualitative labels include supported, partially supported, supported by job description, unverified/unsupported, and inference-related categories. The summary flags prompt engineering, workflow understanding, and AI-agent/automation experience as not explicitly established by the available CV evidence. It also notes that the explanation called Sveaviken PM a best fit without clearly addressing the job's fluent-Swedish requirement, while the CV lists Swedish as beginner.

Because the explanation labels use multiple qualitative categories and have not been consolidated into a consistent scoring scheme, no overall explanation-faithfulness percentage is reported. The claim count should also be reconciled with the CSV, because an earlier draft recorded 18 claims.

### What remains before these results are final

1. Check the four flagged CV QA items against the original CV and complete QA CSV; update labels only when the evidence supports a change.
2. Confirm the five job relevance labels against the full job descriptions and the candidate CV.
3. Reconcile the explanation claim count (18 in the earlier draft versus 19 in the latest summary) with the actual CSV rows.
4. Keep all current scores marked as preliminary until these checks are complete.


## 6. Qualitative Examples from the Initial Evaluation

This section records representative examples from the current manually reviewed outputs. These examples illustrate observed behaviour; they are not a substitute for a larger evaluation set.

### Example A: CV question answered well (QA01)

**Question:** What programming languages and technical skills does the candidate have?

**Observed result:** The answer listed the programming languages and AI/NLP tools recorded in the CV, including Python, SQL, Kotlin, PHP, Java, LLMs, RAG, Transformers, PyTorch, Hugging Face, and Scikit-learn.

**Manual assessment:** Correctness score: 2/2. All 26 counted factual claims were labelled as supported (26/26).

**Interpretation:** This is an example where the system returned a detailed answer that was consistent with the available CV evidence. The claim count and score are based on the current manual annotations and should still be checked against the original CV before final submission.

### Example B: Work experience mixed with extracurricular leadership (QA03)

**Question:** What work experience does the candidate have?

**Observed result:** The answer listed the Service Operations Internship and Research Assistant role, but also included the NSU ACM Student Chapter Team Leader role under work experience.

**Manual assessment:** Correctness score: 1/2. Eight of nine counted factual claims were labelled as supported.

**Issue:** The ACM leadership activity is described in the CV as leadership/extracurricular experience, not a conventional employment role. Including it in the work-experience list blurs the distinction between employment and extracurricular activities.

**Interpretation:** The answer contains mostly supported information, but the way the information is categorized reduces its correctness. The system should separate employment, research, and extracurricular leadership.

### Example C: Research experience misattributed to a job role (QA04)

**Question:** What research experience does the candidate have?

**Observed result:** The answer attributed conversational memory, semantic search, and PDF-based RAG question answering to the Research Assistant role.

**Manual assessment:** Correctness score: 1/2. Four of seven counted factual claims were labelled as supported.

**Issue:** The CV lists the Adaptive Memory Research Assistant as a separate RAG project, while the Research Assistant position at North South University concerned AI techniques for computational fluid dynamics. The answer mixes project experience with employment responsibilities.

**Interpretation:** This is an evidence-attribution problem: information about the candidate may be present in the CV, but the system attaches it to the wrong role.

### Example D: Technology claim not supported by the CV (QA07)

**Question:** What tools and technologies does the candidate have experience with?

**Observed result:** The answer listed several CV technologies and also claimed familiarity with Kubernetes and cloud-native platforms.

**Manual assessment:** Correctness score: 1/2. Thirteen of fourteen counted factual claims were labelled as supported.

**Issue:** Kubernetes and cloud-native platform experience was not established by the available CV evidence.

**Interpretation:** A single unsupported claim can remain important even when most of an answer is supported. The system should avoid adding skills based on job context unless the CV explicitly supports them.

### Example E: Recommendation explanation misses a key eligibility constraint

**Observed result:** In the reviewed multi-job explanation, A Hub and Sveaviken PM were described as the best fits. The explanation identified relevant AI/LLM projects and some job-specific gaps, but did not clearly highlight that Sveaviken PM required fluent Swedish while the CV listed Swedish as beginner.

**Manual review:** The explanation review contains 19 claims with mixed qualitative labels. Six were labelled “Supported”; other claims were partially supported, supported by the job description, inferential, or unverified.

**Issue:** The conclusion emphasized technical overlap without sufficiently accounting for a potentially important language requirement.

**Interpretation:** Recommendation explanations should distinguish technical similarity from overall suitability and explicitly mention mandatory requirements that appear unmet. Because the labels are mixed, no single explanation-faithfulness percentage is reported.

### Qualitative analysis summary

Across these examples, the main observed failure patterns were:

- **Category confusion:** extracurricular or project experience presented as employment responsibilities.
- **Evidence attribution errors:** genuine CV information attached to the wrong role or activity.
- **Unsupported skill claims:** technologies or experience not established by the CV.
- **Incomplete eligibility assessment:** technical similarity emphasized while a key job requirement is omitted.

These findings suggest that the system should ground each claim in the correct CV section and assess mandatory job requirements separately from semantic or technical similarity.


## Step 2 — Selected Qualitative Examples

To complement the aggregate metrics, the following examples were selected from the existing manually scored outputs. They illustrate one comparatively strong answer, one clear unsupported claim, and one recommendation-explanation omission. The examples are illustrative and do not represent an exhaustive review of all system outputs.

### Example 1: Strong CV answer (QA01)

**Question:** What programming languages and technical skills does the candidate have?

**Observed result:** The answer listed programming languages, AI/NLP skills, frameworks, and tools that were recorded in the CV.

**Manual assessment:** Correctness score: **2/2**; **26/26** factual claims labelled as supported (100% claim-level support for this answer in the current scoring file).

**Why it is a positive example:** The answer covers the requested skill categories and mostly stays within the available CV evidence. Its final statement about being well-positioned for industry roles is evaluative rather than a directly verifiable CV fact, so similar summary statements should be distinguished from factual claims.

### Example 2: Unsupported project added to the answer (QA05)

**Question:** Which AI, NLP, or machine learning projects has the candidate worked on?

**Observed result:** The answer correctly mentioned projects such as BanglaDialecto and English-to-Swedish machine translation, but also included an “AI-based Analysis of Test Failures in HIL/SIL Environments” Master's thesis at Toyota.

**Manual assessment:** Correctness score: **1/2**; **6/8** factual claims labelled as supported (75% claim-level support in the current scoring file).

**Why it matters:** The Toyota thesis was not present in the supplied CV information. This is a concrete example of an unsupported project claim that could misrepresent the candidate to an employer. The system should only include projects that can be traced to the CV or clearly label information from another source.

### Example 3: Relevant technical match but missed language requirement (job explanation)

**Observed result:** The generated multi-job explanation presented A Hub and Sveaviken PM as strong fits based on AI/LLM experience. However, it did not clearly flag that the Sveaviken PM job required fluent Swedish while the CV listed Swedish as beginner.

**Manual assessment:** The explanation claim-review file contains **19 claims** with mixed qualitative labels. Because these labels include supported, partially supported, inference, and unverified categories, no single overall explanation-faithfulness percentage is reported.

**Why it matters:** Technical similarity alone is not enough to establish overall job suitability. The explanation should separately evaluate mandatory eligibility requirements—especially language requirements—and clearly identify any mismatch.

### What these examples show

The selected outputs show both strengths and weaknesses: the system can return a well-supported summary of skills, but it can also add a project not established by the CV or omit an important job requirement. Future evaluation should continue to assess factual support, correct attribution to CV sections, and explicit handling of mandatory job requirements.

**Status:** Step 2 qualitative examples drafted. The examples and labels remain preliminary and should be checked against the complete original CV and job descriptions before the final report is submitted.


## Step 3 — Generated Explanation Evaluation (CSV Audit)

The claim-level evaluation CSV was checked against the uploaded summary. The file contains **19 claim rows**. One row had a malformed claim ID (`Etraveli` instead of a claim identifier), so the IDs were normalized to the continuous sequence **C01–C19** in the corrected evaluation CSV. This repairs the row identifiers only; it does not change the evidence labels or rationales.

### Claim label distribution

| Evidence label | Count |
|---|---:|
| Supported | 6 |
| Partially supported | 3 |
| Supported by job description | 2 |
| Unverified / unsupported by available CV evidence | 2 |
| Inference / partially supported | 1 |
| Supported as a gap assessment | 1 |
| Supported in broad terms | 1 |
| Unverified / overgeneralized | 1 |
| Partially supported / evaluative | 1 |
| Partially supported / questionable ranking | 1 |
| **Total** | **19** |

### Main observations

- **Useful evidence matching:** The explanation connected the candidate's LLM/RAG, Python, BanglaDialecto, and sentiment-classification experience to relevant job descriptions.
- **Claims needing stronger evidence:** Prompt-engineering experience and specific AI-agent/automation experience were not established by the CV evidence available for this review. Workflow ownership and client-facing communication were also partly inferential.
- **Mandatory requirement overlooked:** The explanation ranked Sveaviken PM among the best fits without clearly accounting for its fluent-Swedish requirement, while the CV lists Swedish as beginner.
- **Ranking conclusion is debatable:** A Hub has clear technical overlap, but describing both A Hub and Sveaviken as the best fits may overemphasize technical similarity and underweight eligibility constraints.

### Reporting decision

Do **not** report a single overall explanation-faithfulness percentage yet. The 19 rows use different qualitative categories, including factual support, job-description evidence, gap assessments, and evaluative judgments. Combining them into a single numerator and denominator would require a consistent rubric and explicit rules for how each label is scored. Treat this as a preliminary manual claim-level audit, not independently validated ground truth.

**Status:** Step 3 completed for the existing explanation: the CSV row count and claim IDs are reconciled, label distribution is documented, and the main grounding and eligibility issues are recorded. The evidence labels themselves remain preliminary and have not been independently re-annotated.


## Step 4 — Exploratory Ranking Metric

The five-job comparison table contains both a system ranking and preliminary human relevance scores (0–2), so an exploratory **NDCG@5** can be calculated for this one ranked list. The system order was taken from the recorded `System_Rank_1_is_best` column. Human relevance scores were used as graded relevance labels.

### Results

| Metric | Result | Interpretation |
|---|---:|---|
| NDCG@5 | **0.760** | The system ranking is reasonably close to the ideal ordering for this small list, but does not put all highest-rated jobs first. |
| Precision@5 (human score ≥ 1) | **0.800 (4/5)** | Four of the five jobs received at least partial relevance from the manual reviewer. |
| Precision@5 (human score = 2) | **0.400 (2/5)** | Two of the five jobs received the highest human relevance score. |

NDCG@5 was computed with the standard graded gain `2^relevance − 1`, discounted by `log2(rank + 1)`, then divided by the ideal DCG obtained by sorting the same five human scores from highest to lowest. The system order was JOB06 (human score 1), JOB05 (1), JOB04 (2), JOB02 (2), and JOB03 (0). The ideal order would place the two score-2 jobs first.

### Limitations

- These values describe **one list of five jobs for one candidate**, not overall system performance across users or queries.
- Human labels are preliminary and manually assigned. A different relevance rubric or reviewer could change the results.
- Precision@5 depends on the chosen relevance threshold. The ≥1 threshold treats partial relevance as relevant; the =2 threshold counts only the highest-rated jobs. Both are shown to make that choice explicit.
- NDCG@5 is exploratory and should not be compared with results from other systems unless they use the same query, candidate set, relevance labels, and evaluation protocol.

**Status:** An additional ranking metric was feasible and calculated. Report NDCG@5 = 0.760 as a single-list exploratory result only; do not present it as a robust estimate of general ranking quality.


---

# Final Evaluation Summary

## Evaluation procedure

The current evaluation uses three complementary checks:

1. **CV question answering (10 questions):** Answers were manually scored for correctness on a 0–2 scale, and factual claims were labelled for support against the CV information available for the review. Claim-level support and answer-level incidence of unsupported claims are reported separately because they measure different things.
2. **Job recommendations (5 jobs):** Each recommendation was manually assigned a preliminary human relevance score from 0 to 2. The system's displayed relevance score and recorded system rank were compared with these human judgments. Spearman and Kendall correlations were calculated as exploratory comparisons; NDCG@5 and two explicitly defined Precision@5 variants were also calculated for the single ranked list.
3. **Generated job explanation (one explanation covering four jobs):** The explanation was broken into 19 claims and manually checked against the available CV details and job descriptions. Qualitative labels were retained rather than collapsed into a single score because they represent different kinds of evidence and judgment.

All labels were manually assigned. The results are preliminary and should not be treated as independently validated ground truth.

## Consolidated results

| Evaluation area | Current result | Interpretation |
|---|---|---|
| CV QA correctness | 11/20; average 1.1/2 (55%) | Answers were mixed in correctness; the labels still need final verification against the complete CV and QA outputs. |
| CV QA claim-level support | 89/102 claims (87.25%) | Most counted claims were marked supported, but claim-level support alone can hide an unsupported claim within an otherwise good answer. |
| CV QA answer-level unsupported claims | 7/10 answers (70%) contained at least one unsupported claim | Unsupported information appeared across many answers despite the higher claim-level support rate. |
| Job relevance | 5 jobs; average human score 1.2/2 (60%) | The five recommendations received mixed relevance judgments. |
| System–human ranking association | Spearman rho = 0.1054 (p = 0.8660); Kendall tau = 0.0000 (p = 1.0000) | No meaningful ranking association is demonstrated by this very small sample; these tests have low evidential value at n = 5. |
| Single-list ranking metric | NDCG@5 = 0.760 | Exploratory only; it describes this one candidate's five-job list. |
| Precision@5 | 0.800 for human score ≥ 1; 0.400 for human score = 2 | The value depends on whether partial relevance counts as relevant. |
| Generated explanation audit | 19 claims; 6 labelled “Supported” and 13 across other qualitative categories | Do not report an overall faithfulness percentage until a consistent scoring rubric defines how all categories should be grouped. |

## Selected qualitative examples

- **Positive CV QA example (QA01):** The skills answer received 2/2 correctness and 26/26 claims marked supported in the current annotations. This illustrates good evidence alignment, although the broad concluding assessment of industry suitability is evaluative rather than a directly verifiable CV fact.
- **Unsupported CV QA claim (QA05):** The answer introduced an “AI-based Analysis of Test Failures in HIL/SIL Environments” Master's thesis at Toyota, which was not present in the supplied CV information. It received 1/2 correctness and 6/8 claims marked supported in the current annotations.
- **Attribution/category error (QA03–QA04):** The system placed extracurricular ACM leadership under work experience and attributed the separate RAG project to the NSU Research Assistant role, whose described work concerned AI techniques for computational fluid dynamics.
- **Unsupported technology claim (QA07):** Kubernetes/cloud-native familiarity was not established by the CV information available for the review.
- **Job explanation eligibility omission:** The explanation emphasized technical overlap for Sveaviken PM but did not clearly address its fluent-Swedish requirement, while the CV lists Swedish as beginner. This shows why mandatory eligibility constraints should be assessed separately from technical similarity.

## Limitations and interpretation

- The evaluation set is small: 10 CV questions, five job recommendations, and one generated explanation with 19 reviewed claims.
- CV QA claim labels and correctness scores, job relevance scores, and explanation labels are manual and preliminary. The complete original CV, full QA answers, and full job postings should be checked before treating them as final.
- The system's raw relevance scores are not probabilities. Their direction and interpretation should be verified from the implementation before using score magnitude as a confidence estimate.
- NDCG@5 and Precision@5 summarize only one five-job list. They do not establish general performance across candidates, queries, or time periods.
- The Precision@5 results use two thresholds to make the relevance definition explicit. Future evaluations should choose and pre-register one threshold if a single headline metric is needed.
- The explanation labels include direct factual support, job-description evidence, gap assessments, inferences, and evaluative judgments. These should not be combined into a single faithfulness percentage without a shared rubric.
- A stronger evaluation should use more CV questions, more candidates and job lists, independently reviewed relevance labels, a consistent claim-level rubric, and adjudication for disagreements.

## Final conclusion

The preliminary evaluation suggests that Personal Opportunity Radar can identify relevant candidate skills and projects, but it can also add unsupported CV details, attribute experience to the wrong activity, and underemphasize mandatory job requirements. The job-ranking results are mixed, and the ranking metrics are based on only one short list. The appropriate conclusion is that the current system shows useful matching behaviour but needs stronger evidence grounding, explicit eligibility checks, and a larger, consistently labelled evaluation before its overall quality can be established.

**Finalization status:** The report now consolidates the current metrics, evaluation procedure, qualitative examples, ranking metrics, and limitations. Numerical results are preserved as preliminary rather than described as fully verified ground truth.
