# Tailoring Suggestions

**Job:** lucidmotors | Perception Machine Learning Engineer – ADAS
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.523

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for lucidmotors | Perception Machine Learning Engineer – ADAS with a deterministic score of 0.523. It already aligns on deep learning, python, pytorch, tensorflow. The main explicit gaps still showing are c++, mxnet, object detection, segmentation.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: deep learning, python, pytorch, tensorflow.
- Preserve the strongest JD-aligned language already present: deep learning, python, pytorch, tensorflow.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: deep learning, python, pytorch, tensorflow.
- Reuse or strengthen bullets that already prove these JD-aligned terms: python, segmentation.
- Review whether you have truthful evidence for the missing required skills before editing anything: c++, mxnet, object detection, segmentation, tracking.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: c++, mxnet, object detection, segmentation, tracking.
- Do not add unsupported preferred-skill claims: agile development teams, bev transformer models, component and system integration, testing and verification.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['python', 'segmentation']
  - Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
  - Reuse/review this bullet because it already supports: python, segmentation
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst I @ Accenture** | overlaps=['python']
  - Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
  - Reuse/review this bullet because it already supports: python
- **[experience] Data Analyst II @ Accenture** | overlaps=['python']
  - Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
  - Reuse/review this bullet because it already supports: python

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: lucidmotors
Job title: Perception Machine Learning Engineer – ADAS
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.523

Matched required skills: ['deep learning', 'python', 'pytorch', 'tensorflow']
Missing required skills: ['c++', 'mxnet', 'object detection', 'segmentation', 'tracking']
Matched preferred skills: []
Missing preferred skills: ['agile development teams', 'bev transformer models', 'component and system integration', 'testing and verification']
Matched terms: ['deep learning', 'python', 'pytorch', 'tensorflow']
Top dimensions: analytics_ml_depth=1.00/0.116, required_skills_alignment=0.44/0.114, tooling_alignment=1.00/0.093, title_alignment=0.40/0.084, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['python', 'segmentation'] | bullet=Drove lapse and retention risk assessments using Python (gradient boosting) and customer segmentation with SQL, uncovering key drivers of early terminations that informed policy changes and reduced early-lapse rates by 15% Improved quarterly risk assessment accuracy by 12% by implementing a gradient boosting model that predicts policyholder default probabilities, using demographic & historical claim data to refine risk mitigation strategies
2. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Built Python-based validation frameworks to cross-check trial records against regulatory and protocol standards, reducing compliance review time by 35% and improving quality assurance scores by 20%
3. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Deduced key cardiovascular biomarkers in product performance assessments using Python and Tableau, leveraging AWS S3 and Databricks for data, improving early-risk detection accuracy by 14% across 12k+ patient records
4. [experience] Data Analyst I @ Accenture | overlaps=['python'] | bullet=Manipulated and analyzed large-scale clinical and real-world datasets (trial records, biomarker studies) using Python, SQL, and Databricks, ensuring compliance with regulatory standards, improving early risk detection 10%
5. [experience] Data Analyst II @ Accenture | overlaps=['python'] | bullet=Conducted portfolio exposure analysis using Python for scenario modeling, SQL for data aggregation, & Tableau for risk visualization, informing pricing and design changes that improved profitability by 10% and reduced lapse risk by 12%
6. [experience] Data Scientist II (AI Engineer) @ L.B. Foster Salient Systems | overlaps=['pytorch'] | bullet=Fine-tuned a LLaMA-2 model using Hugging Face AutoModelForCausalLM and LoRA adapters in PyTorch Lightning, tracked via MLflow, and deployed through Amazon Bedrock, improving response clarity and alignment by ~20%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return:
1. A 2-3 sentence recruiter-facing summary for why this resume is the best current variant.
2. A short keep/emphasize list grounded in the evidence.
3. A short tailoring list describing what to strengthen or make more explicit, only if truthful.
4. A do-not-claim list for unsupported gaps.
5. 3-5 bullet rewrite directions grounded only in the provided bullets.
```
