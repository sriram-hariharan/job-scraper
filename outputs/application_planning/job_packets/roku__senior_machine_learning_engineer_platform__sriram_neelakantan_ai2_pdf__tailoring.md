# Tailoring Suggestions

**Job:** roku | Senior Machine Learning Engineer, Platform
**Selected resume:** Sriram_Neelakantan_AI2.pdf
**Selected score:** 0.573

## Recruiter Summary
Sriram_Neelakantan_AI2.pdf is the selected variant for roku | Senior Machine Learning Engineer, Platform with a deterministic score of 0.573. It already aligns on generative artificial intelligence, python, pytorch, spark. The main explicit gaps still showing are airflow, aws sagemaker, flink, huggingface.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: generative artificial intelligence, python, pytorch, spark.
- Preserve the strongest JD-aligned language already present: machine learning, generative artificial intelligence, python, pytorch, spark.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: generative artificial intelligence, python, pytorch, spark.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, s3, spark.
- Review whether you have truthful evidence for the missing required skills before editing anything: airflow, aws sagemaker, flink, huggingface, java, kafka.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: airflow, aws sagemaker, flink, huggingface, java, kafka, kotlin, ray.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python', 's3']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python, s3
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst II @ Accenture** | overlaps=['spark']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: spark
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: roku
Job title: Senior Machine Learning Engineer, Platform
Selected resume: Sriram_Neelakantan_AI2.pdf
Selected score: 0.573

Matched required skills: ['generative artificial intelligence', 'python', 'pytorch', 'spark']
Missing required skills: ['airflow', 'aws sagemaker', 'flink', 'huggingface', 'java', 'kafka', 'kotlin', 'ray', 's3', 'scala']
Matched preferred skills: []
Missing preferred skills: []
Matched terms: ['machine learning', 'generative artificial intelligence', 'python', 'pytorch', 'spark']
Top dimensions: analytics_ml_depth=1.00/0.116, title_alignment=0.50/0.105, experimentation_depth=1.00/0.093, required_skills_alignment=0.29/0.073, tooling_alignment=0.75/0.070, domain_relevance=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python', 's3'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards and improving early risk detection by 10%
4. [experience] Data Analyst II @ Accenture | overlaps=['spark'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
5. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing, design changes that improved profitability by 10% and reduced lapse risk by 12%
6. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return:
1. A 2-3 sentence recruiter-facing summary for why this resume is the best current variant.
2. A short keep/emphasize list grounded in the evidence.
3. A short tailoring list describing what to strengthen or make more explicit, only if truthful.
4. A do-not-claim list for unsupported gaps.
5. 3-5 bullet rewrite directions grounded only in the provided bullets.
```
