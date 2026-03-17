# Tailoring Suggestions

**Job:** roku | Research Data Scientist
**Selected resume:** Sriram_Neelakantan_Product_Data_Scientist.pdf
**Selected score:** 0.622

## Recruiter Summary
Sriram_Neelakantan_Product_Data_Scientist.pdf is the selected variant for roku | Research Data Scientist with a deterministic score of 0.622. It already aligns on a/b testing, forecasting, looker, python, r, sql. The main explicit gaps still showing are bayesian inference, causal inference, experimental design, sas.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: a/b testing, forecasting, looker, python, r, sql, tableau.
- Keep preferred-skill evidence visible: machine learning.
- Preserve the strongest JD-aligned language already present: Data Scientist II, a/b testing, forecasting, looker, python, r, sql, tableau.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: a/b testing, forecasting, looker, python, r, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql, tableau.
- Review whether you have truthful evidence for the missing required skills before editing anything: bayesian inference, causal inference, experimental design, sas, statistical modeling.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: bayesian inference, causal inference, experimental design, sas, statistical modeling.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql', 'tableau']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python, sql, tableau
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Science Intern @ Norfolk Southern Corp** | overlaps=['python', 'sql']
  - Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst @ Techmentee Inc.** | overlaps=['python']
  - Cleaned and processed multi-year datasets in Python, performing descriptive statistics and time-trend analyses that informed 8+ stakeholder discussions and were incorporated into draft briefs and presentation materials
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: roku
Job title: Research Data Scientist
Selected resume: Sriram_Neelakantan_Product_Data_Scientist.pdf
Selected score: 0.622

Matched required skills: ['a/b testing', 'forecasting', 'looker', 'python', 'r', 'sql', 'tableau']
Missing required skills: ['bayesian inference', 'causal inference', 'experimental design', 'sas', 'statistical modeling']
Matched preferred skills: ['machine learning']
Missing preferred skills: []
Matched terms: ['Data Scientist II', 'a/b testing', 'forecasting', 'looker', 'python', 'r', 'sql', 'tableau', 'machine learning']
Top dimensions: required_skills_alignment=0.58/0.149, title_alignment=0.67/0.140, preferred_skills_alignment=1.00/0.093, tooling_alignment=0.83/0.078, analytics_ml_depth=0.60/0.070, domain_relevance=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql', 'tableau'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
2. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
3. [experience] Data Science Intern @ Norfolk Southern Corp | overlaps=['python', 'sql'] | bullet=Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
4. [experience] Data Analyst @ Techmentee Inc. | overlaps=['python'] | bullet=Cleaned and processed multi-year datasets in Python, performing descriptive statistics and time-trend analyses that informed 8+ stakeholder discussions and were incorporated into draft briefs and presentation materials
5. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
6. [experience] Data Analyst I @ Accenture | overlaps=['sql'] | bullet=Collaborated on a catalog management efficiency project using SQL, boosting productivity by 25%, orchestrated a quality framework with cross-functional teams, enhancing efficiency by 15%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return:
1. A 2-3 sentence recruiter-facing summary for why this resume is the best current variant.
2. A short keep/emphasize list grounded in the evidence.
3. A short tailoring list describing what to strengthen or make more explicit, only if truthful.
4. A do-not-claim list for unsupported gaps.
5. 3-5 bullet rewrite directions grounded only in the provided bullets.
```
