from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from typing_extensions import TypedDict

from mongodb_vector_test_ui.core.config import Settings, get_settings
from mongodb_vector_test_ui.llm.grounding import (
    GroundedAnswer,
    build_grounded_messages,
    validate_grounded_response,
)
from mongodb_vector_test_ui.llm.providers import ModelProviderAdapter, chat_model_config_from_env
from mongodb_vector_test_ui.retrieval.evidence import select_evidence
from mongodb_vector_test_ui.retrieval.rerankers import create_reranker


class AnswerWorkflowState(TypedDict, total=False):
    question: str
    candidates: list[Mapping[str, Any]]
    settings: Settings
    adapter: ModelProviderAdapter | None
    reranked: list[dict[str, Any]]
    selection: Any
    messages: list[dict[str, str]]
    model_response: str
    answer_result: dict[str, Any]


def synthesize_answer(
    question: str,
    candidates: list[Mapping[str, Any]],
    *,
    settings: Settings | None = None,
    adapter: ModelProviderAdapter | None = None,
) -> dict[str, Any]:
    """Run the grounded answer workflow through LangGraph."""
    graph = _build_answer_graph()
    state = graph.invoke(
        {
            "question": question,
            "candidates": candidates,
            "settings": settings or get_settings(),
            "adapter": adapter,
        }
    )
    return state["answer_result"]


def _build_answer_graph() -> Any:
    from langgraph.graph import END, START, StateGraph

    def rerank_node(state: AnswerWorkflowState) -> dict[str, Any]:
        reranked = create_reranker(settings=state["settings"]).rerank(
            state["question"], state["candidates"], top_k=None
        )
        return {"reranked": reranked}

    def select_evidence_node(state: AnswerWorkflowState) -> dict[str, Any]:
        return {
            "selection": select_evidence(state["reranked"], minimum=3, maximum=5)
        }

    def prepare_prompt_node(state: AnswerWorkflowState) -> dict[str, Any]:
        return {"messages": build_grounded_messages(state["question"], state["selection"])}

    def generate_node(state: AnswerWorkflowState) -> dict[str, Any]:
        adapter = state.get("adapter") or ModelProviderAdapter(state["settings"])
        model = adapter.create_chat_model(chat_model_config_from_env())
        structured_model = model.with_structured_output(GroundedAnswer)
        response = structured_model.invoke(state["messages"])
        if isinstance(response, GroundedAnswer):
            payload = response.model_dump(mode="json")
        elif isinstance(response, Mapping):
            payload = GroundedAnswer.model_validate(response).model_dump(mode="json")
        else:
            raise TypeError("The chat provider did not return the structured answer contract.")
        return {"model_response": json.dumps(payload)}

    def validate_node(state: AnswerWorkflowState) -> dict[str, Any]:
        selection = state["selection"]
        validated = validate_grounded_response(state["model_response"], selection)
        return {
            "answer_result": {
                **validated,
                "candidate_count": len(state["candidates"]),
                "reranked_count": len(state["reranked"]),
                "evidence_count": len(selection.evidence),
                "minimum_evidence_met": selection.minimum_met,
                "results": state["reranked"],
                "evidence": list(selection.evidence),
            }
        }

    def insufficient_evidence_node(state: AnswerWorkflowState) -> dict[str, Any]:
        return {
            "answer_result": {
                "answer": "The indexed sources do not contain enough information to answer this question.",
                "citations": [],
                "insufficient_evidence": True,
                "candidate_count": len(state["candidates"]),
                "reranked_count": len(state["reranked"]),
                "evidence_count": 0,
                "minimum_evidence_met": False,
                "results": state["reranked"],
                "evidence": [],
            }
        }

    def route_after_selection(state: AnswerWorkflowState) -> str:
        return "prepare_prompt" if state["selection"].evidence else "insufficient_evidence"

    workflow = StateGraph(AnswerWorkflowState)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("select_evidence", select_evidence_node)
    workflow.add_node("prepare_prompt", prepare_prompt_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("insufficient_evidence", insufficient_evidence_node)
    workflow.add_edge(START, "rerank")
    workflow.add_edge("rerank", "select_evidence")
    workflow.add_conditional_edges(
        "select_evidence",
        route_after_selection,
        {"prepare_prompt": "prepare_prompt", "insufficient_evidence": "insufficient_evidence"},
    )
    workflow.add_edge("prepare_prompt", "generate")
    workflow.add_edge("generate", "validate")
    workflow.add_edge("validate", END)
    workflow.add_edge("insufficient_evidence", END)
    return workflow.compile()
