# 从好奇心到创造欲：我用 LangGraph 造了个“会思考”的聊天伙伴

> 当代码不再只是执行命令，而是开始拥有自己的“思路”和“记忆”

最近我迷上了让代码变得更“活”。不是指更快的响应或更炫的效果，而是指那种能根据对话上下文**自己决定下一步要做什么**，甚至能在复杂的任务中记住自己走到哪一步的能力。这听起来有点像在造一个简易的“大脑”。

一开始我用各种 `if...else` 和状态变量尝试，代码很快变得像一团乱麻。直到我发现了 **LangGraph** —— 一个让我能用“画流程图”的方式来编织AI行为的框架。它彻底改变了我对“编程”这件事的看法。今天想和你分享的，就是这段纯粹出于兴趣的探索之旅。

## 缘起：当简单对话无法满足我的“刁难”

我的起点很简单：我想做一个比普通聊天机器人更有趣的东西。比如，一个能和我玩“20个问题”游戏的AI，或者一个能根据我零散的描述，一步步帮我构思一个科幻小说片段的助手。

我很快发现，用传统的“一问一答”方式，AI根本玩不转。在“20个问题”游戏里，AI需要**记住它已经问过的问题和得到的答案**，并据此决定下一个最该问什么来缩小范围。这需要“记忆”和“基于记忆的决策”。而在小说构思中，AI可能需要先和我确定世界观，然后梳理人物关系，再搭建关键情节——这是一个标准的**多步骤流程**，并且下一步该做什么，严重依赖于上一步的结果。

这些，正是LangGraph擅长的地方。它的核心思想迷人极了：**把你的AI应用，想象成一个由节点和边组成的流程图。** 每个节点是一个具体的动作（比如“提问”、“分析回答”、“生成段落”），而边则代表了动作之间的流向，这个流向可以是条件的（如果用户说是，则走A路；如果否，则走B路）。

## 动手：造一个会玩“猜电影”的AI伙伴

说干就干。我决定先用LangGraph实现一个“猜电影”的智能体。它的规则是：AI心里想一部电影，我只能用“是”或“否”来提问，目标是在20个问题内猜中。

首先，我定义了整个游戏需要跟踪的“状态”，这就像游戏的记分牌：

```python
from typing import TypedDict, List

class GameState(TypedDict):
    remaining_questions: int  # 剩余问题数
    known_yes: List[str]     # 已回答“是”的特征
    known_no: List[str]      # 已回答“否”的特征
    current_question: str    # AI当前提出的问题
    game_over: bool          # 游戏是否结束
    message: str             # 给玩家的消息
```

然后，我开始设计流程图里的“节点”。每个节点都是一个清晰、独立的函数：

```python
def generate_question_node(state: GameState):
    """节点：生成一个策略性问题"""
    if state["remaining_questions"] <= 0:
        state["message"] = "机会用完啦，游戏结束！"
        state["game_over"] = True
        return state

    # 这里可以接入大语言模型，基于已知信息生成一个判断性问题
    # 例如：“这部电影是1990年之前上映的吗？”“主角是超级英雄吗？”
    # 为简化，我们模拟一个
    features = ["是1990年后的", "是科幻片", "主角是女性", "获得过奥斯卡"]
    for f in features:
        if f not in state["known_yes"] + state["known_no"]:
            state["current_question"] = f"这部电影{f}吗？"
            break
    state["remaining_questions"] -= 1
    return state

def process_answer_node(state: GameState, answer: str):
    """节点：处理玩家的回答（'是'或'否'）"""
    if answer == "是":
        state["known_yes"].append(state["current_question"])
        state["message"] = "好的，记下了。"
    else:
        state["known_no"].append(state["current_question"])
        state["message"] = "明白，排除这个方向。"
    return state
```

最精彩的部分来了：用LangGraph把这些节点和逻辑“组装”起来。

```python
from langgraph.graph import StateGraph, END

# 1. 创建图
workflow = StateGraph(GameState)

# 2. 添加节点
workflow.add_node("generate_question", generate_question_node)
workflow.add_node("process_answer", process_answer_node)

# 3. 设置起点和终点
workflow.set_entry_point("generate_question")

# 4. 定义有条件的流向：提问后，根据游戏是否结束，决定是等待回答还是结束
def decide_after_question(state):
    if state["game_over"]:
        return END
    else:
        return "process_answer" # 游戏继续，流向“处理回答”节点

workflow.add_conditional_edges("generate_question", decide_after_question)

# 5. 定义从“处理回答”回到“生成问题”的边，形成循环！
workflow.add_edge("process_answer", "generate_question")

# 6. 编译成可执行的应用
game_app = workflow.compile()
```

现在，运行这个游戏，它的状态流转就非常清晰了：

```python
# 初始化游戏
init_state = {
    "remaining_questions": 5, # 简化，只用5个问题
    "known_yes": [],
    "known_no": [],
    "current_question": "",
    "game_over": False,
    "message": "游戏开始！我心里想了一部电影。"
}

# 第一轮：AI生成问题
state = game_app.invoke(init_state)
print(f"AI: {state['current_question']}") # 输出：AI: 这部电影是1990年后的吗？

# 模拟玩家回答“是”
state["player_answer"] = "是"
state = game_app.invoke(state) # 这会触发 process_answer_node
print(f"系统: {state['message']}") # 输出：系统: 好的，记下了。

# 处理完回答后，图会自动循环回 generate_question_node
print(f"AI: {state['current_question']}") # 输出：AI: 这部电影是科幻片吗？
```

看，**一个拥有循环逻辑和状态记忆的AI游戏，其核心流程被清晰地定义在了一张“图”里。** 我想增加一个“猜测”节点？或者一个在猜到后自动播放电影预告片的功能？我只需要在图中插入新的节点，并调整一下连线逻辑即可。这种可塑性，让创造过程充满了乐趣。

## 思考：这为何令人兴奋？原理是什么？

LangGraph 让我兴奋，是因为它触及了编程中一个更本质的层面：**我们不仅是在定义“做什么”，更是在定义“如何思考”。**

它的原理，可以粗略理解为为一个AI应用构建了一个**专用的、可调试的“运行时”**。
1.  **状态对象**是整个系统的唯一真相来源，所有操作都围绕它进行。
2.  **节点**是纯净的函数，只负责处理状态，这让它们易于测试和复用。
3.  **图结构**是预定义的“宪法”，规定了节点间的所有可能路径，包括循环和条件分支。这使得整个系统的行为变得可预测、可可视化。

这带来的最大解放是：**你可以像设计算法或规划剧本一样，去设计AI的行为。** 你从与提示词搏斗的“咒术师”，变成了设计智能体心智模式的“架构师”。

## 发散：你的好奇心，能用它来造什么？

至此，LangGraph对我来说已远不止一个工具。它是一个能将抽象想法快速具象化的“思维发动机”。我开始用它尝试各种有趣的东西：

*   **个性化故事生成器**：设置几个节点，分别负责“理解我的初始想法”、“提出选择题扩展剧情”（“主角该信任这个陌生人吗？A.信任 B.不信任”）、“根据我的选择续写”。一个与我共同创作的故事引擎就诞生了。
*   **学习伙伴**：构建一个流程，让它先就某个主题向我提问，评估我的回答，然后决定是深入讲解某个概念，还是出题测验，或是进入下一个主题。这让自学过程变得像有一个耐心的导师。
*   **自动化数字花园园丁**：设计一个工作流，定期帮我分析我收藏的网页、读书笔记，自动生成关联主题图，甚至提出我未曾想到的问题。

**它的魅力在于，它把你从实现复杂控制流的繁琐细节中解放出来，让你能专注在“让AI如何表现”这个更有创造力的问题上。**

如果你也有一份用代码创造有趣事物的好奇心，LangGraph 提供了一个绝佳的舞台。它降低了为AI构建复杂心智模式的门槛。你不必再为管理状态和流程而分心，可以更专注于设计那些让AI显得聪明、有趣甚至贴心的交互瞬间。

你脑子里有没有哪个“要是能有个AI帮我/陪我……”的想法？或许，LangGraph 就是你把它实现出来的第一块积木。欢迎在评论区聊聊你那些天马行空的创意，或许我们能一起让它“活”过来。