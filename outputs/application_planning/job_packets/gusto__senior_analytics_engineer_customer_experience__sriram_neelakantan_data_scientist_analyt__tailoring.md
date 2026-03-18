# Tailoring Suggestions

**Job:** gusto | Senior Analytics Engineer, Customer Experience
**Selected resume:** Sriram_Neelakantan_Data_Scientist_Analytics.pdf
**Selected score:** 0.682

## Recruiter Summary
Sriram_Neelakantan_Data_Scientist_Analytics.pdf is the selected variant for gusto | Senior Analytics Engineer, Customer Experience with a deterministic score of 0.682. It already aligns on python, sql. The main explicit gaps still showing are no major explicit gaps.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: python, sql.
- Preserve the strongest JD-aligned language already present: python, sql.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: python, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, forecasting, sql.

## Do Not Claim
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'forecasting']
  - Developed ARIMA-based time-series forecasting models on 250k+ longitudinal therapy utilization records, enabling early detection of seasonal demand shifts and improving patient access by 8% Identified key cardiovascular biomarkers using Python and Power BI, leveraging Azure Blob Storage and Databricks to improve early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python, forecasting
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, and Power BI for risk visualization, informing pricing and design changes that improved profitability by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations informing policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities using demographic and historical claim data
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Science Intern @ Norfolk Southern Corp** | overlaps=['python', 'sql']
  - Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: gusto
Job title: Senior Analytics Engineer, Customer Experience
Selected resume: Sriram_Neelakantan_Data_Scientist_Analytics.pdf
Selected score: 0.682

Matched required skills: ['python', 'sql']
Missing required skills: []
Matched preferred skills: []
Missing preferred skills: []
Matched terms: ['python', 'sql']
Top dimensions: required_skills_alignment=1.00/0.256, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, title_alignment=0.26/0.054, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python', 'forecasting'] | bullet=Developed ARIMA-based time-series forecasting models on 250k+ longitudinal therapy utilization records, enabling early detection of seasonal demand shifts and improving patient access by 8% Identified key cardiovascular biomarkers using Python and Power BI, leveraging Azure Blob Storage and Databricks to improve early-risk detection accuracy by 14% across 12k+ patient records
2. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, and Power BI for risk visualization, informing pricing and design changes that improved profitability by 10%
3. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations informing policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities using demographic and historical claim data
4. [experience] Data Science Intern @ Norfolk Southern Corp | overlaps=['python', 'sql'] | bullet=Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
5. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
6. [experience] Data Analyst I @ Accenture | overlaps=['sql'] | bullet=Collaborated on a catalog management efficiency project using SQL, boosting productivity by 25% and orchestrating a quality framework that improved process efficiency by 15%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
