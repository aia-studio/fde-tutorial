"""Ch04 引用：从命中的块里挑出原文句子，并校验它确实出现在源文里。"""

from __future__ import annotations

from common.text import split_sentences, tokens


MARK = "处理："


def best_span(text: str, question: str, min_len: int = 24) -> str:
    """只在处理结论里选句，挑与问题重合词最多的一句；太短就并上下一句。"""
    sents = split_sentences(text)
    if not sents:
        return text
    start = next((i for i, s in enumerate(sents) if MARK in s), 0)
    q = set(tokens(question))
    scored = [(sum(1 for t in tokens(s) if t in q), -i, i) for i, s in enumerate(sents) if i >= start]
    _, _, idx = max(scored)
    begin = max(start, idx - 1)
    span = "".join(sents[begin:idx + 1])
    nxt = idx + 1
    while len(span) < min_len and nxt < len(sents):
        span += sents[nxt]
        nxt += 1
    if span.startswith(MARK):
        span = span[len(MARK):]
    return span


def make_citation(hit: dict, question: str) -> dict:
    return {
        "ticket_no": hit["ticket_no"],
        "chunk_id": hit["chunk_id"],
        "quote": best_span(hit["text"], question),
        "score": round(hit.get("score", 0.0), 3),
    }


def verify(quote: str, source_text: str) -> bool:
    """引文必须是原文的连续子串；转述、改写、补字都会在这里失败。"""
    return quote.replace(" ", "") in source_text.replace(" ", "")


def main() -> None:
    from ch03.search import search

    question = "HY-100 保修几年"
    hit = search(question, 1)[0]
    cit = make_citation(hit, question)
    print(f"问题：{question}")
    print(f"引用：{cit['ticket_no']} → {cit['quote']}")
    print(f"校验：{'对齐' if verify(cit['quote'], hit['text']) else '对不齐'}")
    fake = "整机保修五年"
    print(f"改写后的引文：{fake} → {'对齐' if verify(fake, hit['text']) else '对不齐'}")


if __name__ == "__main__":
    main()
