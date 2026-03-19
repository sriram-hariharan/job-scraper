# Tailoring Suggestions

**Job:** waymo | Applied Research Scientist, 3D Object Detection (PhD New Grad)
**Selected resume:** Sriram_Neelakantan_General_Data_Scientist.pdf
**Selected score:** 0.532

## Recruiter Summary
Sriram_Neelakantan_General_Data_Scientist.pdf is the selected variant for waymo | Applied Research Scientist, 3D Object Detection (PhD New Grad) with a deterministic score of 0.532. It already aligns on machine learning, python, pytorch. The main explicit gaps still showing are computer vision, jax.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: machine learning, python, pytorch.
- Preserve the strongest JD-aligned language already present: machine learning, python, pytorch.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: machine learning, python, pytorch.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, machine learning.
- Review whether you have truthful evidence for the missing required skills before editing anything: computer vision, jax.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: computer vision, jax.
- Do not add unsupported preferred-skill claims: aaai, c++, cvpr, eccv, iccv, iclr, icml, icra.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Developed self-service Tableau dashboards standardizing engagement KPIs, reducing manual reporting by 25% Integrated link analysis and XGBoost into healthcare product efficacy models, improving treatment outcome accuracy and reducing false positives by 20% Identified cardiovascular biomarkers using Python statistical analysis and Tableau visualizations, supporting improved healthcare product assessments
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning']
  - Architected ML-driven data pipelines using Apache Spark for insurance campaign response analysis, improving conversion rates by 5.5%
  - Reuse/review this bullet because it already supports: machine learning
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Automated ingestion and transformation of 250k+ customer records weekly using SQL and Python, achieving 98% data quality
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['python']
  - Built scalable data pipelines using Python & PySpark on Databricks with Azure Storage to process 3M+ high-speed sensor records, enabling automated wheel filtering, anomaly detection, poly-curve analysis, and weight calculation
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['python']
  - Performed advanced EDA in Python and PySpark on Databricks to identify trends and anomalies, enabling proactive wheel replacement and optimized maintenance schedules
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: Applied Research Scientist, 3D Object Detection (PhD New Grad)
Selected resume: Sriram_Neelakantan_General_Data_Scientist.pdf
Selected score: 0.532

Matched required skills: ['machine learning', 'python', 'pytorch']
Missing required skills: ['computer vision', 'jax']
Matched preferred skills: []
Missing preferred skills: ['aaai', 'c++', 'cvpr', 'eccv', 'iccv', 'iclr', 'icml', 'icra', 'ijcv', 'iros', 'neurips', 'pami', 'rss']
Matched terms: ['machine learning', 'python', 'pytorch']
Top dimensions: required_skills_alignment=0.60/0.153, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, title_alignment=0.25/0.053, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Developed self-service Tableau dashboards standardizing engagement KPIs, reducing manual reporting by 25% Integrated link analysis and XGBoost into healthcare product efficacy models, improving treatment outcome accuracy and reducing false positives by 20% Identified cardiovascular biomarkers using Python statistical analysis and Tableau visualizations, supporting improved healthcare product assessments
2. [experience] Data Analyst II @ Accenture | overlaps=['machine learning'] | bullet=Architected ML-driven data pipelines using Apache Spark for insurance campaign response analysis, improving conversion rates by 5.5%
3. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Automated ingestion and transformation of 250k+ customer records weekly using SQL and Python, achieving 98% data quality
4. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python'] | bullet=Built scalable data pipelines using Python & PySpark on Databricks with Azure Storage to process 3M+ high-speed sensor records, enabling automated wheel filtering, anomaly detection, poly-curve analysis, and weight calculation
5. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python'] | bullet=Performed advanced EDA in Python and PySpark on Databricks to identify trends and anomalies, enabling proactive wheel replacement and optimized maintenance schedules
6. [experience] Machine Learning Intern @ Norfolk Southern Corp | overlaps=['pytorch'] | bullet=Streamlined EDA using Pandas, NumPy, and Matplotlib to surface 50+ anomalies across 30k+ records, increasing clustering performance by 40% Implemented Faster R-CNN in PyTorch to detect defects in railway components, classifying 1,000+ defects from 7k undercarriage images Improved defect classification accuracy by 12% through advanced image processing techniques including edge detection and segmentation

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
