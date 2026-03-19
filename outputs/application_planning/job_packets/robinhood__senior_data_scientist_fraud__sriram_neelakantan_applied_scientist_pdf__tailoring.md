# Tailoring Suggestions

**Job:** robinhood | Senior Data Scientist, Fraud
**Selected resume:** Sriram_Neelakantan_Applied_Scientist.pdf
**Selected score:** 0.622

## Recruiter Summary
Sriram_Neelakantan_Applied_Scientist.pdf is the selected variant for robinhood | Senior Data Scientist, Fraud with a deterministic score of 0.622. It already aligns on a/b testing, python, sql. The main explicit gaps still showing are anomaly detection, lightgbm, pattern recognition, tensorflow.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: a/b testing, python, sql.
- Preserve the strongest JD-aligned language already present: Data Scientist II, a/b testing, python, sql.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: a/b testing, python, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql, anomaly detection.
- Review whether you have truthful evidence for the missing required skills before editing anything: anomaly detection, lightgbm, pattern recognition, tensorflow, xgboost.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: anomaly detection, lightgbm, pattern recognition, tensorflow, xgboost.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Techmentee Inc.** | overlaps=['python', 'sql']
  - Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Performed lapse & retention risk assessments using Python with gradient boosting and customer segmentation along with SQL, uncovering drivers of early terminations that informed policy changes and cut early-lapse rates by 15%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Science Intern @ Norfolk Southern Corp** | overlaps=['python', 'sql']
  - Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['python', 'sql']
  - Developed Python and SQL-based models and built dashboards in Tableau to visualize fraudulent vendor payments, contract compliance breaches, and predictive expense risks, improving case resolution speed by 20% Implemented automated reconciliation checks across 16 supplier and payroll payment streams, ensuring accurate disbursements and reducing payment disputes by 28%, which improved trust with vendors and employees
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['anomaly detection']
  - Designed and deployed fraud detection models using anomaly detection techniques, identifying 20% more suspicious claim patterns and mitigating financial exposure by an estimated 1200k rupees annually.
  - Reuse/review this bullet because it already supports: anomaly detection

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: robinhood
Job title: Senior Data Scientist, Fraud
Selected resume: Sriram_Neelakantan_Applied_Scientist.pdf
Selected score: 0.622

Matched required skills: ['a/b testing', 'python', 'sql']
Missing required skills: ['anomaly detection', 'lightgbm', 'pattern recognition', 'tensorflow', 'xgboost']
Matched preferred skills: []
Missing preferred skills: []
Matched terms: ['Data Scientist II', 'a/b testing', 'python', 'sql']
Top dimensions: title_alignment=0.72/0.150, required_skills_alignment=0.38/0.096, domain_relevance=1.00/0.093, experimentation_depth=1.00/0.093, tooling_alignment=0.67/0.062, analytics_ml_depth=0.50/0.058

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Techmentee Inc. | overlaps=['python', 'sql'] | bullet=Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
2. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Performed lapse & retention risk assessments using Python with gradient boosting and customer segmentation along with SQL, uncovering drivers of early terminations that informed policy changes and cut early-lapse rates by 15%
3. [experience] Data Science Intern @ Norfolk Southern Corp | overlaps=['python', 'sql'] | bullet=Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
4. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python', 'sql'] | bullet=Developed Python and SQL-based models and built dashboards in Tableau to visualize fraudulent vendor payments, contract compliance breaches, and predictive expense risks, improving case resolution speed by 20% Implemented automated reconciliation checks across 16 supplier and payroll payment streams, ensuring accurate disbursements and reducing payment disputes by 28%, which improved trust with vendors and employees
5. [experience] Data Analyst I @ Accenture | overlaps=['anomaly detection'] | bullet=Designed and deployed fraud detection models using anomaly detection techniques, identifying 20% more suspicious claim patterns and mitigating financial exposure by an estimated 1200k rupees annually.
6. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Developed and automated rule-based validation scripts in Python to cross-verify insurance claims against underwriting guidelines and compliance thresholds, improving review accuracy and reducing manual processing time by 40%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
