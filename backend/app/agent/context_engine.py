import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from sqlmodel import Session

from app.conversations.models import ChatMessage, Conversation, MessageSender
from app.conversations.service import list_messages
from app.providers.base import ModelProvider

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9.-]+")
ENTITY_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9&.-]+(?:\s+[A-Z][A-Za-z0-9&.-]+){0,3}\b")


@dataclass(frozen=True)
class PackedConversationContext:
    system_prompt: str
    persisted_summary: str | None
    recalled_dialogue: list[str]
    recent_dialogue: list[str]
    entity_topics: list[str]

    def as_prompt_sections(self) -> list[str]:
        sections = [f"<SYSTEM_INSTRUCTION>\n{self.system_prompt}\n</SYSTEM_INSTRUCTION>"]
        if self.persisted_summary:
            sections.append(
                "<PERSISTED_CONVERSATION_SUMMARY>\n"
                f"{self.persisted_summary}\n"
                "</PERSISTED_CONVERSATION_SUMMARY>"
            )
        if self.recalled_dialogue:
            sections.append(
                "<RECALLED_DIALOGUE_NOT_EVIDENCE>\n"
                "Earlier assistant statements are context only and are not authoritative evidence.\n"
                + "\n".join(self.recalled_dialogue)
                + "\n</RECALLED_DIALOGUE_NOT_EVIDENCE>"
            )
        if self.recent_dialogue:
            sections.append(
                "<RECENT_DIALOGUE_NOT_EVIDENCE>\n"
                + "\n".join(self.recent_dialogue)
                + "\n</RECENT_DIALOGUE_NOT_EVIDENCE>"
            )
        return sections


def pack_conversation_context(
    session: Session,
    conversation: Conversation,
    current_request: str,
    system_prompt: str,
    model: ModelProvider,
    *,
    recent_pairs: int = 6,
    summary_threshold_messages: int = 16,
) -> PackedConversationContext:
    messages = list_messages(session, conversation.id)
    summary = _persist_summary_if_needed(
        session,
        conversation,
        messages,
        model,
        recent_pairs=recent_pairs,
        threshold=summary_threshold_messages,
    )
    recent_count = recent_pairs * 2
    recent = messages[-recent_count:]
    older = messages[: max(0, len(messages) - recent_count)]
    recalled = _recall_relevant_messages(older, current_request, maximum=4)
    topics = _extract_entity_topics([current_request, *(message.content for message in messages)])
    return PackedConversationContext(
        system_prompt=system_prompt,
        persisted_summary=summary,
        recalled_dialogue=[_label_message(message) for message in recalled],
        recent_dialogue=[_label_message(message) for message in recent],
        entity_topics=topics,
    )


def _persist_summary_if_needed(
    session: Session,
    conversation: Conversation,
    messages: list[ChatMessage],
    model: ModelProvider,
    *,
    recent_pairs: int,
    threshold: int,
) -> str | None:
    if len(messages) < threshold or conversation.summary_message_count >= len(messages) - 2:
        return conversation.summary
    summarize_through = max(0, len(messages) - recent_pairs * 2)
    candidates = messages[conversation.summary_message_count : summarize_through]
    if not candidates:
        return conversation.summary
    transcript = "\n".join(_label_message(message) for message in candidates)
    summary = model.generate_text(
        "Summarize conversation history for future company research. Preserve user objectives, "
        "named companies, hypotheses, decisions, and unresolved questions. Do not turn assistant "
        "claims into evidence. Always retain the previous summary when it remains relevant.",
        f"PREVIOUS SUMMARY:\n{conversation.summary or 'None'}\n\nNEW DIALOGUE:\n{transcript}",
    )
    conversation.summary = summary
    conversation.summary_message_count = summarize_through
    session.add(conversation)
    session.commit()
    return summary


def _recall_relevant_messages(
    messages: list[ChatMessage],
    query: str,
    maximum: int,
) -> list[ChatMessage]:
    if not messages:
        return []
    corpus = [_tokenize(message.content) for message in messages]
    if not any(corpus):
        return []
    scores = BM25Okapi(corpus).get_scores(_tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    selected_indexes = sorted(index for index, score in ranked[:maximum] if score > 0)
    return [messages[index] for index in selected_indexes]


def _extract_entity_topics(texts: list[str]) -> list[str]:
    entities: set[str] = set()
    for text in texts:
        entities.update(match.group(0).strip() for match in ENTITY_PATTERN.finditer(text))
        entities.update(
            token.lower()
            for token in TOKEN_PATTERN.findall(text)
            if "." in token and len(token) <= 255
        )
    return sorted(entities, key=str.lower)[:30]


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _label_message(message: ChatMessage) -> str:
    role = {
        MessageSender.USER: "USER",
        MessageSender.ASSISTANT: "ASSISTANT_CONTEXT_NOT_EVIDENCE",
        MessageSender.SYSTEM: "SYSTEM_HISTORY",
    }[message.sender]
    return f"{role}: {message.content}"
