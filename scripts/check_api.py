"""Check that both API keys work, with one very small request to each service.

OpenAI: lists the models the key can use (free) and asks GPT-6 Luna for one word.
OpenRouter: asks a Qwen model for one word, choosing the cheapest provider that serves
the model in full precision, as the course asks. Both requests use low reasoning effort.
The keys are read from .env; the script prints tokens, cost and provider, never the keys.
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

JUDGE_MODEL = "gpt-6-luna"           # OpenAI project
CODER_MODEL = "qwen/qwen3.8-27b"     # OpenRouter; qwen3.6-27b has no bf16 or fp16 provider
PROMPT = "Answer with one word: what is the capital of Switzerland?"

load_dotenv()


def check_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "OPENAI_API_KEY is missing in .env"
    client = OpenAI(api_key=key)
    luna = [m.id for m in client.models.list() if "luna" in m.id]
    print(f"OpenAI models with 'luna' in the name: {luna or 'none'}")
    model = JUDGE_MODEL if JUDGE_MODEL in luna or not luna else luna[0]
    reply = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        reasoning_effort="low",
    )
    u = reply.usage
    print(f"OpenAI {model}: {reply.choices[0].message.content!r}, "
          f"{u.prompt_tokens} prompt + {u.completion_tokens} completion tokens")
    return None


def check_openrouter():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return "OPENROUTER_API_KEY is missing in .env"
    client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
    reply = client.chat.completions.create(
        model=CODER_MODEL,
        messages=[{"role": "user", "content": PROMPT}],
        extra_body={
            "reasoning": {"effort": "low"},
            "provider": {"sort": "price", "quantizations": ["bf16", "fp16", "fp32"]},
            "usage": {"include": True},
        },
    )
    u = reply.usage
    cost = getattr(u, "cost", None)
    provider = getattr(reply, "provider", None)
    print(f"OpenRouter {CODER_MODEL} via {provider}: {reply.choices[0].message.content!r}, "
          f"{u.prompt_tokens} prompt + {u.completion_tokens} completion tokens, cost {cost} $")
    return None


if __name__ == "__main__":
    problems = []
    for check in (check_openai, check_openrouter):
        try:
            problem = check()
        except Exception as e:  # report the error of one service and still try the other
            problem = f"{check.__name__}: {type(e).__name__}: {e}"
        if problem:
            problems.append(problem)
    print("\n".join(problems) if problems else "Both APIs work.")
    sys.exit(1 if problems else 0)
