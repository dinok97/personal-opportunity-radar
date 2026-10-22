from langchain_core.messages import SystemMessage

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..models.supervisor_output import SupervisorOutput
from ..helpers.profile_util import load_profile_summary
from ..helpers.agent_util import jobs_block
from ..prompts import (
    TITLE_REPLY,
    MANY_JOBS_REPLY,
    ONE_JOB_REPLY,
    NOT_IN_RESULTS_REPLY,
    SUPERVISOR_PROMPT, 
    EMPTY_REPLY,
    OFF_TOPIC_REPLY,
    INVALID_REPLY,
    NO_CV_REPLY,
    OUTSIDE_SWEDEN_REPLY,
    GENERIC_REPLY
)


MAX_ALLOWED_STEPS=3
SUPERVISOR_MAX_TOKENS = 600
SUPERVISOR_TEMP = 0
RETRY_LIMIT=2


def reply(direct_ans: str, off_topic_part: bool = False) -> dict:
    return {"plans": [], "steps": [], "direct_ans": direct_ans,
            "results": [], "jobs": [], "off_topic_part": off_topic_part}


def supervisor_node(state: FlowStep):    
    history = list(state.get("messages", []))[-20:]

    supervisor_prompt = SUPERVISOR_PROMPT.format(
        TITLE_REPLY=TITLE_REPLY,
        NOT_IN_RESULTS_REPLY=NOT_IN_RESULTS_REPLY,
        MANY_JOBS_REPLY=MANY_JOBS_REPLY,
        ONE_JOB_REPLY=ONE_JOB_REPLY,
        OFF_TOPIC_REPLY=OFF_TOPIC_REPLY,
        NO_CV_REPLY=NO_CV_REPLY,
        OUTSIDE_SWEDEN_REPLY=OUTSIDE_SWEDEN_REPLY,
        GENERIC_REPLY=GENERIC_REPLY
    )
    system = supervisor_prompt + load_profile_summary() + jobs_block(state.get('latest_searched_jobs') or [])

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
        
        if result.topic == "other" or result.topic == "invalid" or result.plans or (result.direct_ans or "").strip():
            output = result
            break

    if output is None:
        return reply(EMPTY_REPLY)

    print(output)

    if output.topic == "other":
        return reply(OFF_TOPIC_REPLY)

    if output.topic == "invalid":
        return reply(INVALID_REPLY)

    if output.plans:
        plans = output.plans[:MAX_ALLOWED_STEPS]
        return {"plans": plans, "steps": plans, "direct_ans": "", "results": [], "jobs": [], "off_topic_part": output.off_topic_part}


    return reply((output.direct_ans or "").strip() or EMPTY_REPLY)
    