"""
API Controller providing Chat functionality
"""

import logging
from typing import Optional

from fastapi import Path
from typing_extensions import Annotated

from galaxy.config import GalaxyAppConfiguration
from galaxy.exceptions import ConfigurationError
from galaxy.managers.chat import ChatManager
from galaxy.managers.context import ProvidesUserContext
from galaxy.schema.fields import DecodedDatabaseIdField
from galaxy.schema.schema import ChatPayload
from galaxy.webapps.galaxy.api import (
    depends,
    DependsOnTrans,
)
from . import (
    depends,
    Router,
)

try:
    import openai
except ImportError:
    openai = None

log = logging.getLogger(__name__)

router = Router(tags=["chat"])

JobIdPathParam = Optional[
    Annotated[
        DecodedDatabaseIdField,
        Path(title="Job ID", description="The Job ID the chat response is produced for."),
    ]
]

DEFAULT_PROMPT = """
Please only say that something went wrong when configuing the ai prompt in your response.
"""


@router.cbv
class ChatAPI:
    config: GalaxyAppConfiguration = depends(GalaxyAppConfiguration)
    chat_manager: ChatManager = depends(ChatManager)

    @router.post("/api/chat")
    def query(
        self,
        job_id: JobIdPathParam,
        payload: ChatPayload,
        trans: ProvidesUserContext = DependsOnTrans,
    ) -> str:
        """We're off to ask the wizard"""

        answer = None

        if job_id:
            existing_response = self.chat_manager.get(trans, job_id)
            if existing_response:
                answer = existing_response.response

        if not answer:
            self._ensure_openai_configured()

            messages = self._build_messages(payload, trans)
            log.debug(f"CHATGPT messages: {messages}")

            response = self._call_openai(messages)
            answer = response.choices[0].message.content

            # TODO: Maybe we need to first check if the job_id exists (in the `job` table)?
            if job_id:
                self.chat_manager.create(trans, job_id, answer)

        return answer

    @router.put("/api/chat/{job_id}/feedback")
    def feedback(
        self,
        job_id: JobIdPathParam,
        feedback: int,
        trans: ProvidesUserContext = DependsOnTrans,
    ) -> int:
        """Provide feedback on the chatbot response."""
        chat_response = self.chat_manager.set_feedback(trans, job_id, feedback)
        return chat_response.feedback

    def _ensure_openai_configured(self):
        """Ensure OpenAI is available and configured with an API key."""
        if openai is None:
            raise ConfigurationError("OpenAI is not installed. Please install openai to use this feature.")
        if self.config.openai_api_key is None:
            raise ConfigurationError("OpenAI is not configured for this instance.")
        openai.api_key = self.config.openai_api_key

    def _get_system_prompt(self) -> str:
        """Get the system prompt for OpenAI."""
        return self.config.openai_chat_prompts.get("tool_error", DEFAULT_PROMPT)

    def _build_messages(self, payload: ChatPayload, trans: ProvidesUserContext) -> list:
        """Build the message array to send to OpenAI."""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": payload.query},
        ]

        user_msg = self._get_user_context_message(trans)
        if user_msg:
            messages.append({"role": "system", "content": user_msg})

        return messages

    def _get_user_context_message(self, trans: ProvidesUserContext) -> str:
        """Generate a user context message based on the user's information."""
        user = trans.user
        if user:
            log.debug(f"CHATGPTuser: {user.username}")
            return f"You will address the user as {user.username}"
        return f"You will address the user as Anonymous User"

    def _call_openai(self, messages: list):
        """Send a chat request to OpenAI and handle exceptions."""
        try:
            return openai.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
            )
        except Exception as e:
            log.error(f"Error calling OpenAI: {e}")
            raise ConfigurationError("An error occurred while communicating with OpenAI.")
