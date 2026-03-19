# Tailoring Suggestions

**Job:** waymo | Machine Learning Engineer - Mapping
**Selected resume:** Sriram_Neelakantan_AI1.pdf
**Selected score:** 0.611

## Recruiter Summary
Sriram_Neelakantan_AI1.pdf is the selected variant for waymo | Machine Learning Engineer - Mapping with a deterministic score of 0.611. It already aligns on deep learning, machine learning, pytorch, tensorflow. The main explicit gaps still showing are c++, computer vision, jax.

## Keep / Emphasize
- Keep explicit required-skill evidence visible: deep learning, machine learning, pytorch, tensorflow.
- Keep preferred-skill evidence visible: generative artificial intelligence.
- Preserve the strongest JD-aligned language already present: deep learning, machine learning, pytorch, tensorflow, generative artificial intelligence.

## Tailoring Actions
- Move the strongest already-supported required skills higher in the resume or summary: deep learning, machine learning, pytorch, tensorflow.
- Reuse or strengthen bullets that already prove these JD-aligned terms: machine learning, pytorch.
- Review whether you have truthful evidence for the missing required skills before editing anything: c++, computer vision, jax.
- If you do have truthful evidence for any missing requirement, add it explicitly in bullets/skills; otherwise leave the gap visible instead of inventing coverage.

## Do Not Claim
- Do not claim missing required skills unless you can support them truthfully: c++, computer vision, jax.
- Do not add unsupported preferred-skill claims: domain adaptation, few-shot learning, foundation models, model adaptation, transfer learning, vision-language models.
- Only add or strengthen resume language when it is already truthful and supported by your actual work.

## Bullet Reuse Candidates
- **[experience] Data Analyst II @ Accenture** | overlaps=['machine learning']
  - Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
  - Reuse/review this bullet because it already supports: machine learning
- **[experience] Data Scientist II (AI Engineer) @ L.B. Foster Salient Systems** | overlaps=['pytorch']
  - Fine-tuned a LLaMA-2 model using Hugging Face AutoModelForCausalLM and LoRA adapters in PyTorch Lightning, tracked via MLflow, and deployed through Amazon Bedrock, improving response clarity and alignment by ~20%
  - Reuse/review this bullet because it already supports: pytorch

## LLM Prompt
```text
You are helping tailor a resume for one job.
You must stay grounded only in the provided evidence.
Do not invent skills, tools, projects, outcomes, or responsibilities.

Job company: waymo
Job title: Machine Learning Engineer - Mapping
Selected resume: Sriram_Neelakantan_AI1.pdf
Selected score: 0.611

Matched required skills: ['deep learning', 'machine learning', 'pytorch', 'tensorflow']
Missing required skills: ['c++', 'computer vision', 'jax']
Matched preferred skills: ['generative artificial intelligence']
Missing preferred skills: ['domain adaptation', 'few-shot learning', 'foundation models', 'model adaptation', 'transfer learning', 'vision-language models']
Matched terms: ['deep learning', 'machine learning', 'pytorch', 'tensorflow', 'generative artificial intelligence']
Top dimensions: required_skills_alignment=0.57/0.146, title_alignment=0.60/0.126, analytics_ml_depth=1.00/0.116, tooling_alignment=1.00/0.093, domain_relevance=0.50/0.047, experimentation_depth=0.50/0.047

Best existing bullets to reuse/review:
1. [experience] Data Analyst II @ Accenture | overlaps=['machine learning'] | bullet=Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns
2. [experience] Data Scientist II (AI Engineer) @ L.B. Foster Salient Systems | overlaps=['pytorch'] | bullet=Fine-tuned a LLaMA-2 model using Hugging Face AutoModelForCausalLM and LoRA adapters in PyTorch Lightning, tracked via MLflow, and deployed through Amazon Bedrock, improving response clarity and alignment by ~20%

Guardrail: Only add or strengthen resume language when it is already truthful and supported by your actual work.

Return compact JSON only with:
1. recruiter_summary: max 2 sentences
2. keep_emphasize: max 4 items
3. tailoring_actions: max 4 items
4. do_not_claim: max 4 items
5. rewrite_directions: max 3 items
```
