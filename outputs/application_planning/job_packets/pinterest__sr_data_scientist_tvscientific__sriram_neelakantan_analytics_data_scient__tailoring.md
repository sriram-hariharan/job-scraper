# Tailoring Suggestions

**Job:** pinterest | Sr. Data Scientist, tvScientific
**Selected resume:** Sriram_Neelakantan_Analytics_Data_Scientist.pdf
**Selected score:** 0.685

## Recruiter Summary
Sriram_Neelakantan_Analytics_Data_Scientist.pdf is the selected variant for pinterest | Sr. Data Scientist, tvScientific with a deterministic score of 0.685. It already aligns on machine learning, python. The main explicit gaps still showing are statistics.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: machine learning, python.
- Preserve the strongest JD-aligned language already present: Data Scientist II, machine learning, python, statistics.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: machine learning, python.
- Reuse or strengthen bullets that already prove these JD-aligned terms: machine learning, apache spark, python.
- Review whether you have truthful evidence for the missing required skills before editing anything: statistics.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: statistics.
- Do not add unsupported preferred-skill claims: apache beam, apache spark, aws athena, scala.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning', 'apache spark']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: machine learning, apache spark
- **[experience] Data Analyst @ Techmentee Inc.** | overlaps=['python']
  - Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging Azure Blob storage and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: pinterest
Job title: Sr. Data Scientist, tvScientific
Selected resume: Sriram_Neelakantan_Analytics_Data_Scientist.pdf
Selected score: 0.685

Matched required skills: ['machine learning', 'python']
Missing required skills: ['statistics']
Matched preferred skills: []
Missing preferred skills: ['apache beam', 'apache spark', 'aws athena', 'scala']
Matched terms: ['Data Scientist II', 'machine learning', 'python', 'statistics']
Top dimensions: required_skills_alignment=1.00/0.256, title_alignment=0.72/0.150, tooling_alignment=1.00/0.093, analytics_ml_depth=0.60/0.070, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['machine learning', 'apache spark'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
2. [experience] Data Analyst @ Techmentee Inc. | overlaps=['python'] | bullet=Assessed acquisition funnel efficiency for a user subscription platform by comparing paid and organic cohorts in SQL and Python, enabling budget reallocations that reduced cost per signup by 10%
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
4. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging Azure Blob storage and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
5. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
6. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
