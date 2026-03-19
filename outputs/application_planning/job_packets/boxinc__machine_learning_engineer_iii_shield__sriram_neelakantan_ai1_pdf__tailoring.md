# Tailoring Suggestions

**Job:** boxinc | Machine Learning Engineer III, Shield
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.506

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for boxinc | Machine Learning Engineer III, Shield with a deterministic score of 0.506. It already aligns on core requirements. The main explicit gaps still showing are dataflow.

## Keep / Emphasize
- Keep preferred-skill evidence visible: bigquery, python, pytorch, tensorflow.
- Preserve the strongest JD-aligned language already present: machine learning, bigquery, python, pytorch, tensorflow.

## Tailoring Actions
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, apache spark.
- Review whether you have truthful evidence for the missing required skills before editing anything: dataflow.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: dataflow.
- Do not add unsupported preferred-skill claims: apache spark, aws sagemaker, azure machine learning, gcp, java, kubernetes, scala.
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
- **[experience] Data Analyst II @ Accenture** | overlaps=['apache spark']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: apache spark
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: boxinc
Job title: Machine Learning Engineer III, Shield
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.506

Matched required skills: []
Missing required skills: ['dataflow']
Matched preferred skills: ['bigquery', 'python', 'pytorch', 'tensorflow']
Missing preferred skills: ['apache spark', 'aws sagemaker', 'azure machine learning', 'gcp', 'java', 'kubernetes', 'scala']
Matched terms: ['machine learning', 'bigquery', 'python', 'pytorch', 'tensorflow']
Top dimensions: title_alignment=0.70/0.147, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047, preferred_skills_alignment=0.36/0.034

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
4. [experience] Data Analyst II @ Accenture | overlaps=['apache spark'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
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
