# Tailoring Suggestions

**Job:** waymo | Data Scientist
**Selected resume:** Sriram_Neelakantan_Analytics_Data_Scientist.pdf
**Selected score:** 0.643

## Recruiter Summary
Sriram_Neelakantan_Analytics_Data_Scientist.pdf is the selected variant for waymo | Data Scientist with a deterministic score of 0.643. It already aligns on python, r, sql. The main explicit gaps still showing are advanced statistical methods.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: python, r, sql.
- Preserve the strongest JD-aligned language already present: Data Scientist II, python, r, sql.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: python, r, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql.
- Review whether you have truthful evidence for the missing required skills before editing anything: advanced statistical methods.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: advanced statistical methods.
- Do not add unsupported preferred-skill claims: advanced machine learning, traffic modeling.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst @ Techmentee Inc.** | overlaps=['python', 'sql']
  - Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'sql']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes, reduced early-lapse rates 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Science Intern @ Norfolk Southern Corp** | overlaps=['python', 'sql']
  - Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
  - Reuse/review this bullet because it already supports: python, sql

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: Data Scientist
Selected resume: Sriram_Neelakantan_Analytics_Data_Scientist.pdf
Selected score: 0.643

Matched required skills: ['python', 'r', 'sql']
Missing required skills: ['advanced statistical methods']
Matched preferred skills: []
Missing preferred skills: ['advanced machine learning', 'traffic modeling']
Matched terms: ['Data Scientist II', 'python', 'r', 'sql']
Top dimensions: required_skills_alignment=0.75/0.192, title_alignment=0.90/0.187, tooling_alignment=1.00/0.093, analytics_ml_depth=0.47/0.054, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst @ Techmentee Inc. | overlaps=['python', 'sql'] | bullet=Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
2. [experience] Data Analyst I @ Accenture | overlaps=['python', 'sql'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
3. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
4. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes, reduced early-lapse rates 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
5. [experience] Data Science Intern @ Norfolk Southern Corp | overlaps=['python', 'sql'] | bullet=Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
6. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
