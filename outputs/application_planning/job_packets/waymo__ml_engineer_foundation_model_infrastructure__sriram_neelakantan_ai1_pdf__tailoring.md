# Tailoring Suggestions

**Job:** waymo | ML Engineer, Foundation Model Infrastructure
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.505

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for waymo | ML Engineer, Foundation Model Infrastructure with a deterministic score of 0.505. It already aligns on python, spark, tensorflow. The main explicit gaps still showing are borg, c++, flume, jax.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: python, spark, tensorflow.
- Keep preferred-skill evidence visible: pytorch.
- Preserve the strongest JD-aligned language already present: python, spark, tensorflow, pytorch.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: python, spark, tensorflow.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, spark.
- Review whether you have truthful evidence for the missing required skills before editing anything: borg, c++, flume, jax, kubeflow.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: borg, c++, flume, jax, kubeflow.
- Do not add unsupported preferred-skill claims: av planning, distributed systems, experiment tracking, model versioning.
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
- **[experience] Data Analyst II @ Accenture** | overlaps=['spark']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: spark
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: ML Engineer, Foundation Model Infrastructure
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.505

Matched required skills: ['python', 'spark', 'tensorflow']
Missing required skills: ['borg', 'c++', 'flume', 'jax', 'kubeflow']
Matched preferred skills: ['pytorch']
Missing preferred skills: ['av planning', 'distributed systems', 'experiment tracking', 'model versioning']
Matched terms: ['python', 'spark', 'tensorflow', 'pytorch']
Top dimensions: analytics_ml_depth=1.00/0.116, title_alignment=0.53/0.112, required_skills_alignment=0.38/0.096, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, project_relevance=0.50/0.023

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
4. [experience] Data Analyst II @ Accenture | overlaps=['spark'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
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
