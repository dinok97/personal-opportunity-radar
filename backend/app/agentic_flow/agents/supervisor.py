from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..prompts import DEFAULT_REPLY, SUPERVISOR_PROMPT, EMPTY_REPLY
from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..models.supervisor_output import SupervisorOutput
from ..helpers.profile_util import load_profile_summary


MAX_ALLOWED_STEPS=3
SUPERVISOR_MAX_TOKENS = 400
SUPERVISOR_TEMP = 0


def supervisor_node(state: FlowStep):
    history = list(state.get("messages", []))[-20:]
    system = SUPERVISOR_PROMPT + load_profile_summary()

    messages = [SystemMessage(content=system), 
                *history]

    llm = get_groq(temp=SUPERVISOR_TEMP, max_tokens=SUPERVISOR_MAX_TOKENS)
    llm_with_structured_output = llm.with_structured_output(SupervisorOutput)

    output: SupervisorOutput = llm_with_structured_output.invoke(messages)

    print(output)

    if output.plans:
        print(output.plans[:MAX_ALLOWED_STEPS])
        plans = output.plans[:MAX_ALLOWED_STEPS]
        return {"plans": plans, "steps": plans, "direct_ans": "", "results": [], "jobs": []}

    reply = (output.direct_ans or "").strip()
    if not reply:
        print("Supervisor returned neither plans nor a reply")
        reply = EMPTY_REPLY

    return {"plans": [], "steps": [], "direct_ans": reply, "results": [], "jobs": []}
    