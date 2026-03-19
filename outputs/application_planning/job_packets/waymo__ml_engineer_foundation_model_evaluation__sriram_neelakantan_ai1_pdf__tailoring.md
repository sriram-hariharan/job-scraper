# Tailoring Suggestions

**Job:** waymo | ML Engineer, Foundation Model Evaluation
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.537

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for waymo | ML Engineer, Foundation Model Evaluation with a deterministic score of 0.537. It already aligns on machine learning, python, pytorch, tensorflow. The main explicit gaps still showing are evaluation, jax, robotics.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: machine learning, python, pytorch, tensorflow.
- Preserve the strongest JD-aligned language already present: machine learning, python, pytorch, tensorflow.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: machine learning, python, pytorch, tensorflow.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, machine learning.
- Review whether you have truthful evidence for the missing required skills before editing anything: evaluation, jax, robotics.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: evaluation, jax, robotics.
- Do not add unsupported preferred-skill claims: av planning, c++, open source projects.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: machine learning
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: ML Engineer, Foundation Model Evaluation
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.537

Matched required skills: ['machine learning', 'python', 'pytorch', 'tensorflow']
Missing required skills: ['evaluation', 'jax', 'robotics']
Matched preferred skills: []
Missing preferred skills: ['av planning', 'c++', 'open source projects']
Matched terms: ['machine learning', 'python', 'pytorch', 'tensorflow']
Top dimensions: required_skills_alignment=0.57/0.146, analytics_ml_depth=1.00/0.116, title_alignment=0.53/0.112, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, project_relevance=0.50/0.023

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
4. [experience] Data Analyst II @ Accenture | overlaps=['machine learning'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
5. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
6. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
