from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv()
print(os.getenv("GROQ_API_KEY"))    

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

r = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"user","content":"say hello"}]
)

print(r.choices[0].message.content)