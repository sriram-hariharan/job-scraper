# Tailoring Suggestions

**Job:** brex | Data Analyst II
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.586

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for brex | Data Analyst II with a deterministic score of 0.586. It already aligns on sql, generative artificial intelligence, python, tableau. The main explicit gaps still showing are claude code, cursor, github copilot, hex.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: sql, generative artificial intelligence, python, tableau.
- Keep preferred-skill evidence visible: bigquery, databricks.
- Preserve the strongest JD-aligned language already present: Data Analyst II, sql, generative artificial intelligence, python, tableau, bigquery, databricks.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: sql, generative artificial intelligence, python, tableau.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, tableau, databricks, sql.
- Review whether you have truthful evidence for the missing required skills before editing anything: claude code, cursor, github copilot, hex, looker.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: claude code, cursor, github copilot, hex, looker.
- Do not add unsupported preferred-skill claims: airflow, dbt, snowflake.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'tableau', 'databricks']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python, tableau, databricks
- **[experience] Data Analyst I @ Accenture** | overlaps=['sql', 'python', 'databricks']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
  - Reuse/review this bullet because it already supports: sql, python, databricks
- **[experience] Data Analyst II @ Accenture** | overlaps=['sql', 'python', 'tableau']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: sql, python, tableau
- **[experience] Data Analyst II @ Accenture** | overlaps=['sql', 'python']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
  - Reuse/review this bullet because it already supports: sql, python
- **[experience] Data Scientist II (AI Engineer) @ L.B. Foster Salient Systems** | overlaps=['sql', 'databricks']
  - Partnered with railway clients, operations teams, engineering leads to gather requirements, deliver custom Power BI dashboards (integrated with SQL queries from Databricks) for maintenance KPIs tailored to stakeholder needs
  - Reuse/review this bullet because it already supports: sql, databricks

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: brex
Job title: Data Analyst II
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.586

Matched required skills: ['sql', 'generative artificial intelligence', 'python', 'tableau']
Missing required skills: ['claude code', 'cursor', 'github copilot', 'hex', 'looker']
Matched preferred skills: ['bigquery', 'databricks']
Missing preferred skills: ['airflow', 'dbt', 'snowflake']
Matched terms: ['Data Analyst II', 'sql', 'generative artificial intelligence', 'python', 'tableau', 'bigquery', 'databricks']
Top dimensions: title_alignment=1.00/0.209, required_skills_alignment=0.44/0.114, analytics_ml_depth=0.50/0.058, tooling_alignment=0.56/0.052, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python', 'tableau', 'databricks'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
2. [experience] Data Analyst I @ Accenture | overlaps=['sql', 'python', 'databricks'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
3. [experience] Data Analyst II @ Accenture | overlaps=['sql', 'python', 'tableau'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
4. [experience] Data Analyst II @ Accenture | overlaps=['sql', 'python'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
5. [experience] Data Scientist II (AI Engineer) @ L.B. Foster Salient Systems | overlaps=['sql', 'databricks'] | bullet=Partnered with railway clients, operations teams, engineering leads to gather requirements, deliver custom Power BI dashboards (integrated with SQL queries from Databricks) for maintenance KPIs tailored to stakeholder needs
6. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return:
1. A 2-3 sentence recruiter-facing summary for why this resume is the best current variant.
2. A short keep/emphasize list grounded in the evidence.
3. A short tailoring list describing what to strengthen or make more explicit, only if truthful.
4. A do-not-claim list for unsupported gaps.
5. 3-5 bullet rewrite directions grounded only in the provided bullets.
```
