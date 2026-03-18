# Tailoring Suggestions

**Job:** stripe | PhD Machine Learning Engineer, New Grad
**Selected resume:** Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
**Selected score:** 0.608

## Recruiter Summary
Neelakantan_SriramHariharan_Resume_MLE_v3.pdf is the selected variant for stripe | PhD Machine Learning Engineer, New Grad with a deterministic score of 0.608. It already aligns on numpy, pandas, python, scikit-learn, spark. The main explicit gaps still showing are github repositories, scala, stackoverflow contributions.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: numpy, pandas, python, scikit-learn, spark.
- Preserve the strongest JD-aligned language already present: machine learning engineer, numpy, pandas, python, scikit-learn, spark.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: numpy, pandas, python, scikit-learn, spark.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, spark, numpy, pandas.
- Review whether you have truthful evidence for the missing required skills before editing anything: github repositories, scala, stackoverflow contributions.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: github repositories, scala, stackoverflow contributions.
- Do not add unsupported preferred-skill claims: large language models, machine learning operations, pull requests, reinforcement learning, test coverage, unsupervised learning.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'spark']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
  - Reuse/review this bullet because it already supports: python, spark
- **[experience] Machine Learning @ Norfolk Southern Corp** | overlaps=['numpy', 'pandas']
  - Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety
  - Reuse/review this bullet because it already supports: numpy, pandas
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Scientist II @ L.B. Foster Salient Systems** | overlaps=['python']
  - Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: stripe
Job title: PhD Machine Learning Engineer, New Grad
Selected resume: Neelakantan_SriramHariharan_Resume_MLE_v3.pdf
Selected score: 0.608

Matched required skills: ['numpy', 'pandas', 'python', 'scikit-learn', 'spark']
Missing required skills: ['github repositories', 'scala', 'stackoverflow contributions']
Matched preferred skills: []
Missing preferred skills: ['large language models', 'machine learning operations', 'pull requests', 'reinforcement learning', 'test coverage', 'unsupervised learning']
Matched terms: ['machine learning engineer', 'numpy', 'pandas', 'python', 'scikit-learn', 'spark']
Top dimensions: required_skills_alignment=0.62/0.160, title_alignment=0.58/0.122, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['python', 'spark'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic and historical claim data to refine risk mitigation strategies Identified key features causing customer early lapse through lapse analysis, reporting findings using Python, SQL, and Tableau to the cross-functional Finance team, by refining pricing strategies
2. [experience] Machine Learning @ Norfolk Southern Corp | overlaps=['numpy', 'pandas'] | bullet=Streamlined Exploratory Data Analysis with Pandas, NumPy, and Matplotlib to pinpoint over 50 anomalies among 30,000+ data points, achieving a 40% boost in clustering accuracy and optimizing project deliverables Implemented Faster R-CNN using PyTorch for railway defect (in coaches, tracks, plates, etc) detection, categorizing over 1000 defects from 7k undercarriage camera images, helping enhance maintenance precision & safety
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key biomarkers linked to cardiovascular health in healthcare product performance assessments by using Python for statistical analysis and Tableau for data visualizations, with AWS S3 and Databricks for data storage
4. [experience] Data Scientist II @ L.B. Foster Salient Systems | overlaps=['python'] | bullet=Built a scalable data pipeline using Python & PySpark on Databricks with Azure Blob Storage to process 3M+ high- speed sensor data, enabling automated wheel filtering, anomaly detection, poly curve analysis, & weight calculation.

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
