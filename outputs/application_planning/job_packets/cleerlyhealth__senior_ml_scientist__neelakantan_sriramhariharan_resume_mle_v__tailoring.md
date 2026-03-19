# Tailoring Suggestions

**Job:** cleerlyhealth | Senior ML Scientist
**Selected resume:** Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
**Selected score:** 0.599

## Recruiter Summary
Neelakantan_SriramHariharan_Resume_MLE_v3.pdf is the selected variant for cleerlyhealth | Senior ML Scientist with a deterministic score of 0.599. It already aligns on classification, deep learning, machine learning, python. The main explicit gaps still showing are applied mathematics, detection, image science, reconstruction.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: classification, deep learning, machine learning, python.
- Preserve the strongest JD-aligned language already present: Machine Learning, classification, deep learning, machine learning, python.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: classification, deep learning, machine learning, python.
- Reuse or strengthen bullets that already prove these JD-aligned terms: machine learning, python, detection.
- Review whether you have truthful evidence for the missing required skills before editing anything: applied mathematics, detection, image science, reconstruction, registration, segmentation.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: applied mathematics, detection, image science, reconstruction, registration, segmentation.
- Do not add unsupported preferred-skill claims: confluence/jira, continuous learning techniques, ct imaging, google workspace, incremental learning, semi-supervised/self-supervised/unsupervised learning, slack, vision transformers.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning', 'python']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
  - Reuse/review this bullet because it already supports: machine learning, python
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['detection', 'python']
  - Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.
  - Reuse/review this bullet because it already supports: detection, python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
  - Reuse/review this bullet because it already supports: python
- **[experience] Machine Learning @ Norfolk Southern Corp** | overlaps=['detection']
  - Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety
  - Reuse/review this bullet because it already supports: detection

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: cleerlyhealth
Job title: Senior ML Scientist
Selected resume: Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
Selected score: 0.599

Matched required skills: ['classification', 'deep learning', 'machine learning', 'python']
Missing required skills: ['applied mathematics', 'detection', 'image science', 'reconstruction', 'registration', 'segmentation']
Matched preferred skills: []
Missing preferred skills: ['confluence/jira', 'continuous learning techniques', 'ct imaging', 'google workspace', 'incremental learning', 'semi-supervised/self-supervised/unsupervised learning', 'slack', 'vision transformers', 'zoom video']
Matched terms: ['Machine Learning', 'classification', 'deep learning', 'machine learning', 'python']
Top dimensions: title_alignment=0.82/0.171, analytics_ml_depth=1.00/0.116, required_skills_alignment=0.40/0.102, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['machine learning', 'python'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
2. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['detection', 'python'] | bullet=Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
4. [experience] Machine Learning @ Norfolk Southern Corp | overlaps=['detection'] | bullet=Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
