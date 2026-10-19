from langchain_core.messages import SystemMessage

from ..prompts import SUPERVISOR_PROMPT, EMPTY_REPLY
from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..models.supervisor_output import SupervisorOutput
from ..helpers.profile_util import load_profile_summary
from ..helpers.agent_util import jobs_block


MAX_ALLOWED_STEPS=3
SUPERVISOR_MAX_TOKENS = 400
SUPERVISOR_TEMP = 0
RETRY_LIMIT=2


def supervisor_node(state: FlowStep):    
    history = list(state.get("messages", []))[-20:]
    system = SUPERVISOR_PROMPT + load_profile_summary() + jobs_block(state.get('latest_searched_jobs') or [])

    messages = [SystemMessage(content=system), 
                *history]

    llm = get_groq(temp=SUPERVISOR_TEMP, max_tokens=SUPERVISOR_MAX_TOKENS)
    llm_with_structured_output = llm.with_structured_output(SupervisorOutput)

    output: SupervisorOutput | None = None
    for _ in range(RETRY_LIMIT):
        try:
            result = llm_with_structured_output.invoke(messages)
        except Exception as e:
            print("Supervisor failed: %s", e)
            continue
        
        if result.plans or (result.direct_ans or "").strip():
            output = result
            break  

    if output is None:
        return {"plans": [], "steps": [], "direct_ans": EMPTY_REPLY, "results": [], "jobs": []}

    if output.plans:
        plans = output.plans[:MAX_ALLOWED_STEPS]
        return {"plans": plans, "steps": plans, "direct_ans": "", "results": [], "jobs": []}


    return {"plans": [], "steps": [], "direct_ans": output.direct_ans.strip() or EMPTY_REPLY, "results": [], "jobs": []}
    