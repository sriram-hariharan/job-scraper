# Tailoring Suggestions

**Job:** chime | Data Analyst, Lending
**Selected resume:** Sriram_Neelakantan_Data_Analyst.pdf
**Selected score:** 0.639

## Recruiter Summary
Sriram_Neelakantan_Data_Analyst.pdf is the selected variant for chime | Data Analyst, Lending with a deterministic score of 0.639. It already aligns on python, sql, tableau. The main explicit gaps still showing are looker.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: python, sql, tableau.
- Preserve the strongest JD-aligned language already present: Sr. Data Analyst, python, sql, tableau, experimentation.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: python, sql, tableau.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, sql.
- Review whether you have truthful evidence for the missing required skills before editing anything: looker.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: looker.
- Do not add unsupported preferred-skill claims: causal thinking, experimentation, statistical analysis.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'sql']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes, reduced early-lapse rates 15%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Science Intern @ Norfolk Southern Corp** | overlaps=['python', 'sql']
  - Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Sr. Data Analyst @ Techmentee Inc.** | overlaps=['python', 'sql']
  - Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
  - Reuse/review this bullet because it already supports: python, sql
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: chime
Job title: Data Analyst, Lending
Selected resume: Sriram_Neelakantan_Data_Analyst.pdf
Selected score: 0.639

Matched required skills: ['python', 'sql', 'tableau']
Missing required skills: ['looker']
Matched preferred skills: []
Missing preferred skills: ['causal thinking', 'experimentation', 'statistical analysis']
Matched terms: ['Sr. Data Analyst', 'python', 'sql', 'tableau', 'experimentation']
Top dimensions: required_skills_alignment=0.75/0.192, title_alignment=0.77/0.160, experimentation_depth=1.00/0.093, tooling_alignment=0.75/0.070, domain_relevance=0.50/0.047, preferred_skills_alignment=0.33/0.031

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python', 'sql'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
2. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes, reduced early-lapse rates 15%
3. [experience] Data Science Intern @ Norfolk Southern Corp | overlaps=['python', 'sql'] | bullet=Designed automated SQL and Python validation scripts to flag suspicious freight invoices, duplicate debits, and noncompliant payroll entries, improving fraud detection coverage and reducing investigation cycle times by 10 hours weekly
4. [experience] Sr. Data Analyst @ Techmentee Inc. | overlaps=['python', 'sql'] | bullet=Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
5. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
6. [experience] Data Analyst I @ Accenture | overlaps=['sql'] | bullet=Optimized catalog management workflows using SQL, increasing operational productivity by 25%, and implemented a cross-functional quality framework that improved process efficiency by 15%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
