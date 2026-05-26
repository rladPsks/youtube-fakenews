import json
import random
import re
import gc
from collections import Counter
import time

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen3.5-4B"

K_SAMPLES = 7
SEED = 42

MAX_INPUT_CHARS = 4000
MAX_NEW_TOKENS = 160
MAX_REASON_CHARS = 120

TEMPERATURE = 0.5
TOP_P = 0.8
TOP_K = 20

tokenizer = None
model = None


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(SEED)


def truncate_text_for_model(text, max_chars):
    text = str(text).strip()

    if len(text) <= max_chars:
        return text

    head = max_chars // 3
    tail = max_chars // 3
    middle = max_chars - head - tail
    mid_start = max(0, len(text) // 2 - middle // 2)

    return (
        text[:head]
        + "\n...\n[중간 생략]\n...\n"
        + text[mid_start: mid_start + middle]
        + "\n...\n[중간 생략]\n...\n"
        + text[-tail:]
    )


def build_prompt(title, transcript):
    transcript = truncate_text_for_model(transcript, MAX_INPUT_CHARS)

    return f"""
너는 한국어 유튜브 자막의 진위 판별기다.

판정 기준:
- 사실 기반이면 answer=1
- 허위/왜곡/조작이면 answer=0

판정 시 주의:
- 단순 오타, STT 인식 오류, 띄어쓰기 오류, HTML 엔티티 문제만으로 허위/왜곡으로 판단하지 마라.
- 자막에 일부 어색한 표현이 있어도 핵심 주장, 수치, 사건 설명이 사실 기반이면 answer=1로 판단하라.
- answer=0은 핵심 주장 자체가 허위, 왜곡, 조작, 음모론, 근거 없는 단정일 때 선택하라.
- reasoning에는 단순 오타나 자막 품질 문제를 주요 근거로 쓰지 마라.

다음 조건을 만족하는 reasoning을 생성하라:
- 반드시 80자 이상 120자 이하
- 최소 2개 이상의 근거 포함
- 각 근거는 명확히 구분되도록 작성
- 추상적 표현 금지
- 구체적인 판단 이유 제시

[출력 규칙 - 매우 중요]
- 반드시 JSON 한 줄만 출력하라
- JSON 앞뒤에 다른 문장, 설명, 줄바꿈을 붙이지 마라
- answer는 숫자 0 또는 1만 사용하라
- reasoning은 반드시 한국어 한 문장, 80자 이상 120자 이하로 써라
- reasoning은 반드시 큰따옴표 안에 넣어라
- 장황한 설명, 단계별 사고 과정, 분석 과정은 쓰지 마라

출력 예시:
{{"answer": 0, "reasoning": "자막에 검증되지 않은 단정과 과장된 표현이 반복되고, 구체적 출처나 수치 근거가 부족해 허위 가능성이 높다고 판단된다."}}
{{"answer": 1, "reasoning": "자막이 질병 원인과 증상처럼 확인 가능한 정보를 중심으로 설명하고, 과장된 음모론이나 조작 주장이 없어 사실 기반으로 판단된다."}}

제목:
{title}

자막:
{transcript}

JSON:
""".strip()


def clean_reasoning(reason, max_chars=MAX_REASON_CHARS):
    reason = re.sub(r"\s+", " ", str(reason).strip())
    return reason[:max_chars]


def parse_output(text):
    text = str(text).strip()

    try:
        obj = json.loads(text)
        answer = obj.get("answer", None)
        reasoning = obj.get("reasoning", "")

        if str(answer).strip() in ["0", "1"]:
            answer = int(answer)
            return {
                "answer": answer,
                "label": 1 - answer,
                "label_name": "REAL" if answer == 1 else "FAKE",
                "reason": clean_reasoning(reasoning),
                "raw_output": text,
            }
    except Exception:
        pass

    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)

    if match:
        try:
            obj = json.loads(match.group(0))
            answer = obj.get("answer", None)
            reasoning = obj.get("reasoning", "")

            if str(answer).strip() in ["0", "1"]:
                answer = int(answer)
                return {
                    "answer": answer,
                    "label": 1 - answer,
                    "label_name": "REAL" if answer == 1 else "FAKE",
                    "reason": clean_reasoning(reasoning),
                    "raw_output": text,
                }
        except Exception:
            pass

    answer_match = re.search(
        r'["\']?answer["\']?\s*[:=]\s*["\']?([01])["\']?',
        text,
        flags=re.IGNORECASE,
    )

    reasoning_match = re.search(
        r'["\']?reasoning["\']?\s*[:=]\s*["\']([^"\']{0,300})["\']',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if answer_match:
        answer = int(answer_match.group(1))
        reasoning = reasoning_match.group(1) if reasoning_match else ""

        return {
            "answer": answer,
            "label": 1 - answer,
            "label_name": "REAL" if answer == 1 else "FAKE",
            "reason": clean_reasoning(reasoning),
            "raw_output": text,
        }

    return {
        "answer": None,
        "label": None,
        "label_name": "UNKNOWN",
        "reason": "",
        "raw_output": text,
    }


def load_model():
    global tokenizer, model

    if tokenizer is None or model is None:
        print("[INFO] Loading Qwen model...")

        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
        )

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model.eval()

        print("[INFO] Qwen model loaded.")
        print("CUDA:", torch.cuda.is_available())
        print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

    return tokenizer, model


def generate(prompt):
    tokenizer, model = load_model()

    messages = [
        {"role": "system", "content": "You are a concise classifier. /no_think"},
        {"role": "user", "content": prompt + "\n/no_think"},
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
    ).to(model.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            pad_token_id=tokenizer.eos_token_id,
        )

    gen = out[0][inputs["input_ids"].shape[1]:]

    return tokenizer.decode(gen, skip_special_tokens=True).strip()


def run_qwen_7_samples(title: str, transcript: str):
    outputs = []
    prompt = build_prompt(title, transcript)

    start_time = time.time()
    TIMEOUT_SECONDS = 600

    for k in range(K_SAMPLES):
        if time.time() - start_time > TIMEOUT_SECONDS:
            raise RuntimeError("QWEN_TIMEOUT")

        print(f"[INFO] Qwen generation {k + 1}/{K_SAMPLES}")

        raw = generate(prompt)
        parsed = parse_output(raw)

        outputs.append(parsed)

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return outputs