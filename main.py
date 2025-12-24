from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GameState(TypedDict):
    remaining_questions: int
    known_yes: List[str]
    known_no: List[str]
    current_question: str
    game_over: bool
    message: str
    player_answer: str
    features: List[str]

def generate_question_node(state: GameState):
    if state["remaining_questions"] <= 0:
        state["message"] = "机会用完啦，游戏结束！"
        state["game_over"] = True
        return state
    asked = state["known_yes"] + state["known_no"]
    next_q = None
    for f in state["features"]:
        if f not in asked:
            next_q = f
            break
    if next_q is None:
        state["message"] = "没有新的问题，游戏结束！"
        state["game_over"] = True
        return state
    state["current_question"] = f"这部电影{next_q}吗？"
    state["remaining_questions"] -= 1
    state["message"] = "请回答 是 或 否"
    return state

def process_answer_node(state: GameState):
    ans = state.get("player_answer", "")
    feature = state["current_question"].replace("这部电影", "").replace("吗？", "")
    if ans == "是":
        state["known_yes"].append(feature)
        state["message"] = "好的，记下了。"
    else:
        state["known_no"].append(feature)
        state["message"] = "明白，排除这个方向。"
    state["player_answer"] = ""
    return state

def decide_after_question(state: GameState):
    if state["game_over"]:
        return END
    return "process_answer"

workflow = StateGraph(GameState)
workflow.add_node("generate_question", generate_question_node)
workflow.add_node("process_answer", process_answer_node)
workflow.set_entry_point("generate_question")
workflow.add_conditional_edges("generate_question", decide_after_question)
workflow.add_edge("process_answer", "generate_question")
game_app = workflow.compile()

def run_demo():
    state = {
        "remaining_questions": 5,
        "known_yes": [],
        "known_no": [],
        "current_question": "",
        "game_over": False,
        "message": "游戏开始！我心里想了一部电影。",
        "player_answer": "",
        "features": ["是1990年后的", "是科幻片", "主角是女性", "获得过奥斯卡"]
    }
    state = game_app.invoke(state)
    print(f"AI: {state['current_question']}")

def run_cli(questions: int, features: List[str]):
    state = {
        "remaining_questions": questions,
        "known_yes": [],
        "known_no": [],
        "current_question": "",
        "game_over": False,
        "message": "",
        "player_answer": "",
        "features": features
    }
    state = game_app.invoke(state)
    while not state["game_over"]:
        print(f"AI: {state['current_question']}")
        ans = input("你的回答(是/否，q退出): ").strip().lower()
        if ans in ["q", "quit", "exit"]:
            break
        if ans in ["是", "y", "yes"]:
            state["player_answer"] = "是"
        elif ans in ["否", "n", "no"]:
            state["player_answer"] = "否"
        else:
            print("请输入 是 或 否")
            continue
        state = game_app.invoke(state)
        if state["game_over"]:
            print("系统: 机会用完啦，游戏结束！")
            break
    print(f"已知是: {state['known_yes']}")
    print(f"已知否: {state['known_no']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--questions", type=int, default=10)
    parser.add_argument("--features", type=str, default="")
    args = parser.parse_args()
    if args.demo:
        run_demo()
    else:
        feats = [s.strip() for s in args.features.split(",") if s.strip()]
        if not feats:
            feats = ["是1990年后的", "是科幻片", "主角是女性", "获得过奥斯卡"]
        run_cli(args.questions, feats)
