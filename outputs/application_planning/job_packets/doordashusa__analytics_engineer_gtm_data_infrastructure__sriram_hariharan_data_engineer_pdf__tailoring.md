# Tailoring Suggestions

**Job:** doordashusa | Analytics Engineer, GTM Data Infrastructure
**Selected resume:** Sriram_Hariharan_Data_Engineer.pdf
**Selected score:** 0.631

## Recruiter Summary
Sriram_Hariharan_Data_Engineer.pdf is the selected variant for doordashusa | Analytics Engineer, GTM Data Infrastructure with a deterministic score of 0.631. It already aligns on airflow, python, sql. The main explicit gaps still showing are no major explicit gaps.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: airflow, python, sql.
- Preserve the strongest JD-aligned language already present: airflow, python, sql.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: airflow, python, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql, aws.

## Do Not Claim
- Do not add unsupported preferred-skill claims: aws, ci/cd, infrastructure as code, sigma, tableau.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Techmentee Inc.** | overlaps=['python', 'sql']
  - Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['aws']
  - Collaborated with cross-functional teams to implement a data lake architecture using AWS S3 in combination with AWS Glue and Athena, improving catalog management efficiency by 25% through enhanced data accessibility
  - Reuse/review this bullet because it already supports: aws
- **[experience] Data Analyst I @ Accenture** | overlaps=['aws']
  - Established a real-time forecasting system utilizing AWS Athena, which processed over 250k records and enabled faster trend identification, leading to a gross margin increase of 8% through more responsive market strategies
  - Reuse/review this bullet because it already supports: aws
- **[experience] Data Analyst II @ Accenture** | overlaps=['aws']
  - Designed an event-driven data integration pipeline using AWS Step Functions and AWS Batch to coordinate ingestion and transformation tasks across systems, improving decision-making speed and accuracy by 12%
  - Reuse/review this bullet because it already supports: aws
- **[experience] Data Analyst II @ Accenture** | overlaps=['sql']
  - Enhanced customer lapse detection and analysis by implementing SQL-based workflows, providing the Finance team with real-time insights into customer behavior and enabling more effective, data-driven pricing strategies
  - Reuse/review this bullet because it already supports: sql

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: doordashusa
Job title: Analytics Engineer, GTM Data Infrastructure
Selected resume: Sriram_Hariharan_Data_Engineer.pdf
Selected score: 0.631

Matched required skills: ['airflow', 'python', 'sql']
Missing required skills: []
Matched preferred skills: []
Missing preferred skills: ['aws', 'ci/cd', 'infrastructure as code', 'sigma', 'tableau']
Matched terms: ['airflow', 'python', 'sql']
Top dimensions: required_skills_alignment=1.00/0.256, analytics_ml_depth=1.00/0.116, title_alignment=0.35/0.073, tooling_alignment=0.75/0.070, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Techmentee Inc. | overlaps=['python', 'sql'] | bullet=Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
2. [experience] Data Analyst I @ Accenture | overlaps=['aws'] | bullet=Collaborated with cross-functional teams to implement a data lake architecture using AWS S3 in combination with AWS Glue and Athena, improving catalog management efficiency by 25% through enhanced data accessibility
3. [experience] Data Analyst I @ Accenture | overlaps=['aws'] | bullet=Established a real-time forecasting system utilizing AWS Athena, which processed over 250k records and enabled faster trend identification, leading to a gross margin increase of 8% through more responsive market strategies
4. [experience] Data Analyst II @ Accenture | overlaps=['aws'] | bullet=Designed an event-driven data integration pipeline using AWS Step Functions and AWS Batch to coordinate ingestion and transformation tasks across systems, improving decision-making speed and accuracy by 12%
5. [experience] Data Analyst II @ Accenture | overlaps=['sql'] | bullet=Enhanced customer lapse detection and analysis by implementing SQL-based workflows, providing the Finance team with real-time insights into customer behavior and enabling more effective, data-driven pricing strategies
6. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python'] | bullet=Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high-speed sensor data, for automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
