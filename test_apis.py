

from openai import OpenAI
client = OpenAI(api_key="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")
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Write a haiku about recursion in programming."
        }
    ]
)

print(completion.choices[0].message)