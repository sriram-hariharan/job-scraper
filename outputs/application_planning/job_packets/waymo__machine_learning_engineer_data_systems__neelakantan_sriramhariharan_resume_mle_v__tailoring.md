# Tailoring Suggestions

**Job:** waymo | Machine Learning Engineer, Data & Systems
**Selected resume:** Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
**Selected score:** 0.592

## Recruiter Summary
Neelakantan_SriramHariharan_Resume_MLE_v3.pdf is the selected variant for waymo | Machine Learning Engineer, Data & Systems with a deterministic score of 0.592. It already aligns on machine learning, python, pytorch. The main explicit gaps still showing are computer vision, data mining, jax.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: machine learning, python, pytorch.
- Preserve the strongest JD-aligned language already present: machine learning engineer, machine learning, python, pytorch.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: machine learning, python, pytorch.
- Reuse or strengthen bullets that already prove these JD-aligned terms: machine learning, python, pytorch.
- Review whether you have truthful evidence for the missing required skills before editing anything: computer vision, data mining, jax.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: computer vision, data mining, jax.
- Do not add unsupported preferred-skill claims: c++.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning', 'python']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
  - Reuse/review this bullet because it already supports: machine learning, python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['python']
  - Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.
  - Reuse/review this bullet because it already supports: python
- **[experience] Machine Learning @ Norfolk Southern Corp** | overlaps=['pytorch']
  - Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety
  - Reuse/review this bullet because it already supports: pytorch

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: Machine Learning Engineer, Data & Systems
Selected resume: Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
Selected score: 0.592

Matched required skills: ['machine learning', 'python', 'pytorch']
Missing required skills: ['computer vision', 'data mining', 'jax']
Matched preferred skills: []
Missing preferred skills: ['c++']
Matched terms: ['machine learning engineer', 'machine learning', 'python', 'pytorch']
Top dimensions: title_alignment=0.66/0.138, required_skills_alignment=0.50/0.128, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['machine learning', 'python'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
3. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python'] | bullet=Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.
4. [experience] Machine Learning @ Norfolk Southern Corp | overlaps=['pytorch'] | bullet=Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
