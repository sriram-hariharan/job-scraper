# Tailoring Suggestions

**Job:** sofi | Marketing Data Scientist, Reporting
**Selected resume:** Sriram_Neelakantan_AI2.pdf
**Selected score:** 0.597

## Recruiter Summary
Sriram_Neelakantan_AI2.pdf is the selected variant for sofi | Marketing Data Scientist, Reporting with a deterministic score of 0.597. It already aligns on analytics, data analysis, data science, python, sql, tableau. The main explicit gaps still showing are airflow, business logic, data engineering, data quality.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: analytics, data analysis, data science, python, sql, tableau.
- Preserve the strongest JD-aligned language already present: Sr. Data Scientist, analytics, data analysis, data science, python, sql, tableau.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: analytics, data analysis, data science, python, sql, tableau.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql, tableau.
- Review whether you have truthful evidence for the missing required skills before editing anything: airflow, business logic, data engineering, data quality, data stacks, dbt.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: airflow, business logic, data engineering, data quality, data stacks, dbt, pipeline development, snowflake.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql', 'tableau']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python, sql, tableau
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'tableau']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python, tableau
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'sql']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: sofi
Job title: Marketing Data Scientist, Reporting
Selected resume: Sriram_Neelakantan_AI2.pdf
Selected score: 0.597

Matched required skills: ['analytics', 'data analysis', 'data science', 'python', 'sql', 'tableau']
Missing required skills: ['airflow', 'business logic', 'data engineering', 'data quality', 'data stacks', 'dbt', 'pipeline development', 'snowflake', 'structured datasets']
Matched preferred skills: []
Missing preferred skills: []
Matched terms: ['Sr. Data Scientist', 'analytics', 'data analysis', 'data science', 'python', 'sql', 'tableau']
Top dimensions: title_alignment=0.59/0.123, analytics_ml_depth=1.00/0.116, required_skills_alignment=0.40/0.102, experimentation_depth=1.00/0.093, domain_relevance=0.50/0.047, preferred_skills_alignment=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql', 'tableau'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
2. [experience] Data Analyst I @ Accenture | overlaps=['python', 'tableau'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
3. [experience] Data Analyst I @ Accenture | overlaps=['python', 'sql'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
4. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
5. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
6. [experience] Data Analyst I @ Accenture | overlaps=['sql'] | bullet=Collaborated on a catalog management efficiency project using SQL, boosting productivity by 25%, orchestrated a quality framework with cross-functional teams, enhancing efficiency by 15%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
