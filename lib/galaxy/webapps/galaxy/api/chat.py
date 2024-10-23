"""
API Controller providing Chat functionality
"""
import logging

try:
    import openai
except ImportError:
    openai = None

from galaxy.config import GalaxyAppConfiguration
from galaxy.managers.context import ProvidesUserContext
from galaxy.webapps.galaxy.api import (
    depends,
    DependsOnTrans,
)
from galaxy.exceptions import ConfigurationError
from galaxy.schema.schema import ChatPayload
from . import (
    depends,
    Router,
)

log = logging.getLogger(__name__)

router = Router(tags=["chat"])

PROMPT = """
Adopt the persona of an galaxy project expert who is able to easily explain complex terminal error messages to users, but do so in a dry and serious manner.
 Focus on providing clear and concise explanations that are easy to understand. 
 You will be provided with a standard error output and should attempt to explain how this error happened and how to fix it within Galaxy.
 If you are unsure totally sure of how to fix the error, please direct the user https://help.galaxyproject.org/ to ask a human for help.
 Please ensure your response is in well formated markdown.
"""
@router.cbv
class ChatAPI:
    config: GalaxyAppConfiguration = depends(GalaxyAppConfiguration)

    @router.post("/api/chat")
    def query(self, query: ChatPayload, trans: ProvidesUserContext = DependsOnTrans) -> str:
        """We're off to ask the wizard"""

        if openai is None:
            raise ConfigurationError("OpenAI is not installed. Please install openai to use this feature.")
        if openai is None or self.config.openai_api_key is None:
            raise ConfigurationError("OpenAI is not configured for this instance.")
        else:
            openai.api_key = self.config.openai_api_key

        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": query.query},
        ]

        if query.context == "username":
            user = trans.user
            if user is not None:
                log.debug(f"CHATGPTuser: {user.username}")
                msg = f"You will address the user as {user.username}"
            else:
                msg = f"You will address the user as Anonymous User"
            messages.append({"role": "system", "content": msg})
        # elif query.context == "tool_error":
        #     msg = "The user will provide you a Galaxy tool error, and you will try to debug and explain what happened"
        #     messages.append({"role": "system", "content": msg})

        log.debug(f"CHATGPTmessages: {messages}")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        print(response)

        answer = response.choices[0].message.content
        print(answer)
        return answer