import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

messages_plain = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Return one short answer only."
    },
    {
        "role": "user",
        "content": "Rewrite this bullet naturally in one line without changing meaning: "
                   "'Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns'"
    },
]

messages_json = [
    {
        "role": "system",
        "content": (
            "Return exactly one JSON object. "
            "Do not use markdown. "
            'Format: {"abstain": false, "abstain_reason": "", "options": [{"patch_text": "...", "reason": "..."}]}'
        ),
    },
    {
        "role": "user",
        "content": (
            "Original bullet: Architected a data pipeline using supervised ML models and Apache Spark "
            "for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns\n\n"
            "Deterministic draft: Architected a data pipeline using supervised machine learning models and Apache Spark "
            "for insurance campaign response studies, enhancing conversion rates by 5.5% through customized campaigns\n\n"
            "Return at most 2 better options, or abstain."
        ),
    },
]

def dump_response(label, completion):
    print("\n" + "=" * 120)
    print(label)
    print("=" * 120)

    choice = completion.choices[0]
    message = choice.message

    print("finish_reason:", getattr(choice, "finish_reason", None))
    print("content repr:", repr(getattr(message, "content", None)))
    print("reasoning repr:", repr(getattr(message, "reasoning", None)))
    print("refusal repr:", repr(getattr(message, "refusal", None)))

    if hasattr(message, "model_dump"):
        print("message dump:")
        print(json.dumps(message.model_dump(), indent=2, default=str))
    else:
        print("message object:", message)

# 1) Plain text test
completion_plain = client.chat.completions.create(
    model=MODEL,
    messages=messages_plain,
    temperature=0,
    max_completion_tokens=220,
    include_reasoning=False,
)
dump_response("PLAIN TEXT TEST", completion_plain)

# # 2) JSON object mode test
# completion_json = client.chat.completions.create(
#     model=MODEL,
#     messages=messages_json,
#     temperature=0,
#     max_completion_tokens=320,
#     include_reasoning=False,
#     response_format={"type": "json_object"},
# )
# dump_response("JSON OBJECT TEST", completion_json)

messages_judge = [
    {
        "role": "system",
        "content": (
            "You are the judge stage for one resume bullet rewrite. "
            "Return plain text only. "
            "Do not use markdown. "
            "Use exactly these lines:\n"
            "WINNER: deterministic | writer_option_1 | writer_option_2 | abstain\n"
            "REASON: <one short sentence>\n"
            "REJECTED: <comma-separated option ids or none>\n"
            "QUALITY_FLAGS: <comma-separated tags or none>"
        ),
    },
    {
        "role": "user",
        "content": (
            "Original bullet:\n"
            "Architected a data pipeline using supervised ML models and Apache Spark for insurance campaign response studies, "
            "enhancing conversion rates by 5.5% through customized campaigns\n\n"
            "Deterministic draft:\n"
            "Architected a data pipeline using supervised machine learning models and Apache Spark for insurance campaign response studies, "
            "enhancing conversion rates by 5.5% through customized campaigns\n\n"
            "writer_option_1:\n"
            "Architected a data pipeline with supervised ML models and Apache Spark for insurance campaign response studies, "
            "raising conversion rates by 5.5% through customized campaigns\n\n"
            "Pick the winner."
        ),
    },
]

completion_judge = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages_judge,
    temperature=0,
    max_completion_tokens=500,
)
dump_response("JUDGE PLAIN TEXT TEST", completion_judge)