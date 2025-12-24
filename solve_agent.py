import os
import re
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    question: str
    answer: str
    need_clarification: bool
    chunks: List[Dict[str, Any]]
    history: List[Dict[str, Any]]

def list_md_files(root: str) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".venv" in dirpath or "venv" in dirpath:
            continue
        for f in filenames:
            if f.lower().endswith(".md"):
                files.append(os.path.join(dirpath, f))
    return files

def tokenize(text: str) -> List[str]:
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    hans = [c for c in text if "\u4e00" <= c <= "\u9fff"]
    return list(set(words + hans))

def split_chunks(path: str) -> List[Dict[str, Any]]:
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    start = 1
    buf: List[str] = []
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("#") and buf:
            chunks.append({"file": path, "start": start, "end": i - 1, "text": "".join(buf)})
            buf = [line]
            start = i
        else:
            buf.append(line)
    if buf:
        chunks.append({"file": path, "start": start, "end": len(lines), "text": "".join(buf)})
    return chunks

def score_chunk(q_tokens: List[str], text: str) -> int:
    t_tokens = tokenize(text)
    return len(set(q_tokens) & set(t_tokens))

def retrieve(state: AgentState) -> AgentState:
    q = state.get("question", "").strip()
    q_tokens = tokenize(q)
    all_files = list_md_files(os.getcwd())
    all_chunks: List[Dict[str, Any]] = []
    for path in all_files:
        for ch in split_chunks(path):
            ch["score"] = score_chunk(q_tokens, ch["text"])
            all_chunks.append(ch)
    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    top = [c for c in all_chunks if c["score"] > 0][:3]
    state["chunks"] = top
    return state

def decide(state: AgentState):
    if state.get("chunks"):
        return "answer"
    return "clarify"

def answer_node(state: AgentState) -> AgentState:
    parts = []
    for ch in state["chunks"]:
        text = ch["text"]
        lines = [l for l in text.splitlines() if l.strip()]
        sel = []
        q_tokens = tokenize(state["question"])
        for ln in lines:
            if len(set(tokenize(ln)) & set(q_tokens)) >= 1:
                sel.append(ln)
        if not sel:
            sel = lines[:3]
        snippet = "\n".join(sel[:5])
        ref = f"{ch['file']}:{ch['start']}"
        parts.append(f"{snippet}\n来源: {ref}")
    state["answer"] = "\n\n".join(parts) if parts else "未找到相关内容"
    state["need_clarification"] = False
    state["history"].append({"q": state["question"], "a": state["answer"]})
    return state

def clarify_node(state: AgentState) -> AgentState:
    state["answer"] = "未找到相关内容，请提供更具体的关键词或上下文。"
    state["need_clarification"] = True
    return state

workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("answer", answer_node)
workflow.add_node("clarify", clarify_node)
workflow.set_entry_point("retrieve")
workflow.add_conditional_edges("retrieve", decide)
app = workflow.compile()

def run_cli():
    history: List[Dict[str, Any]] = []
    while True:
        q = input("请输入你的问题(q退出): ").strip()
        if q.lower() in ["q", "quit", "exit"]:
            break
        state: AgentState = {"question": q, "answer": "", "need_clarification": False, "chunks": [], "history": history}
        state = app.invoke(state)
        print(state["answer"])
        history = state["history"]

def run_once(question: str) -> str:
    state: AgentState = {"question": question, "answer": "", "need_clarification": False, "chunks": [], "history": []}
    state = app.invoke(state)
    return state["answer"]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=str, default="")
    args = parser.parse_args()
    if args.question:
        print(run_once(args.question))
    else:
        run_cli()
