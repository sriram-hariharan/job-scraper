# Tailoring Suggestions

**Job:** avepoint | Product Data Scientist
**Selected resume:** Sriram_Neelakantan_AI2.pdf
**Selected score:** 0.619

## Recruiter Summary
Sriram_Neelakantan_AI2.pdf is the selected variant for avepoint | Product Data Scientist with a deterministic score of 0.619. It already aligns on causal inference, machine learning, python, sql. The main explicit gaps still showing are data visualization tools, experiment design, statistical modeling.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: causal inference, machine learning, python, sql.
- Keep preferred-skill evidence visible: power bi, tableau.
- Preserve the strongest JD-aligned language already present: Sr. Data Scientist, causal inference, machine learning, python, sql, power bi, tableau.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: causal inference, machine learning, python, sql.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, aws, tableau, sql.
- Review whether you have truthful evidence for the missing required skills before editing anything: data visualization tools, experiment design, statistical modeling.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: data visualization tools, experiment design, statistical modeling.
- Do not add unsupported preferred-skill claims: amplitude, aws, azure, gainsight, gcp, mixpanel.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 'aws', 'tableau']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python, aws, tableau
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'sql', 'tableau']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python, sql, tableau
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

Job company: avepoint
Job title: Product Data Scientist
Selected resume: Sriram_Neelakantan_AI2.pdf
Selected score: 0.619

Matched required skills: ['causal inference', 'machine learning', 'python', 'sql']
Missing required skills: ['data visualization tools', 'experiment design', 'statistical modeling']
Matched preferred skills: ['power bi', 'tableau']
Missing preferred skills: ['amplitude', 'aws', 'azure', 'gainsight', 'gcp', 'mixpanel']
Matched terms: ['Sr. Data Scientist', 'causal inference', 'machine learning', 'python', 'sql', 'power bi', 'tableau']
Top dimensions: required_skills_alignment=0.57/0.146, title_alignment=0.67/0.140, experimentation_depth=1.00/0.093, tooling_alignment=1.00/0.093, analytics_ml_depth=0.47/0.054, domain_relevance=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python', 'aws', 'tableau'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
2. [experience] Data Analyst II @ Accenture | overlaps=['python', 'sql', 'tableau'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
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
