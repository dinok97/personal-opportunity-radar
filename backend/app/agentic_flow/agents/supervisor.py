from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..prompts import DEFAULT_REPLY, SUPERVISOR_PROMPT
from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..models.supervisor_output import SupervisorOutput


MAX_ALLOWED_STEPS=3
SUPERVISOR_MAX_TOKENS = 300
SUPERVISOR_TEMP = 0


def supervisor_node(state: FlowStep):
    question = state["question"]
    history = list(state.get("messages", []))[-5:]

    messages = [SystemMessage(content=SUPERVISOR_PROMPT), 
                *history, 
                 HumanMessage(content=question)]

    llm = get_groq(temp=SUPERVISOR_TEMP, max_tokens=SUPERVISOR_MAX_TOKENS)
    llm_with_structured_output = llm.with_structured_output(SupervisorOutput, method="json_schema")

    output: SupervisorOutput = llm_with_structured_output.invoke(messages)

    if output.plans:
        print(output.plans[:MAX_ALLOWED_STEPS])
        plans = output.plans[:MAX_ALLOWED_STEPS]
        return {"plans": plans, "steps": plans, "direct_ans": "", "results": []}

    reply = output.direct_ans.strip() or DEFAULT_REPLY
    return {"plans": [], "steps": [], "direct_ans": reply, "results": []}
    