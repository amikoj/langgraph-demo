# LangGraph 猜电影交互示例

## 环境准备
- `py -m venv .venv`
- `.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt`

## 运行
- 交互模式：
  - `.\\.venv\\Scripts\\python.exe main.py`
  - 可选参数：
    - `--questions <数字>` 设置最多提问次数，默认 10
    - `--features "<特征1,特征2,...>"` 设置候选特征列表（逗号分隔）
    - `--answers "<是/否,...>"` 预置回答序列（支持 `是/否`、`y/yes`、`n/no`）
  - 示例：
    - `.\\.venv\\Scripts\\python.exe main.py --questions 5 --features "是科幻片,主角是女性,获得过奥斯卡"`
    - `.\\.venv\\Scripts\\python.exe main.py --questions 3 --features "是1990年后的,是科幻片,主角是女性" --answers "是,否,是"`
- 演示模式（只打印首个问题）：
  - `.\\.venv\\Scripts\\python.exe main.py --demo`

## 工作流说明
- 使用 `StateGraph` 构建两个节点：
  - 生成问题节点：根据已知信息选择下一条未问过的特征
  - 处理回答节点：记录“是/否”，并回到生成问题形成闭环
- 通过条件与循环边实现“结束/继续”的状态流转
