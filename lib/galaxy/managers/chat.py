from typing import Optional

from fastapi import Path
from sqlalchemy import select
from sqlalchemy.exc import (
    MultipleResultsFound,
    NoResultFound,
)
from typing_extensions import Annotated

from galaxy.exceptions import (
    InconsistentDatabase,
    InternalServerError,
    RequestParameterInvalidException,
)
from galaxy.managers import base
from galaxy.managers.context import ProvidesUserContext
from galaxy.model import ChatGXYResponse
from galaxy.model.base import transaction
from galaxy.schema.fields import DecodedDatabaseIdField
from galaxy.util import unicodify

JobIdPathParam = Optional[
    Annotated[
        DecodedDatabaseIdField,
        Path(title="Job ID", description="The Job ID the chat response is produced for."),
    ]
]


def get_chat_responses(session):
    stmt = select(ChatGXYResponse)
    return session.scalars(stmt)


def get_filtered_chat_responses(session, filter):
    stmt = select(ChatGXYResponse).filter_by(**filter)
    return session.scalars(stmt)


def get_response_for_job_id(trans, job_id):
    """Get a ChatGXYResponse from the database by job_id."""
    response = trans.sa_session.query(ChatGXYResponse).get(trans.security.decode_id(job_id))
    if not response:
        return trans.show_error_message(f"Response not found for job id ({str(job_id)})")
    return response


class ChatManager(base.ModelManager[ChatGXYResponse]):
    """
    Business logic for chat responses.
    """

    model_class = ChatGXYResponse

    def create(self, trans: ProvidesUserContext, job_id: JobIdPathParam, response: str) -> ChatGXYResponse:
        """
        Create a new chat response in the DB.

        :param  job_id:      id of the job to associate the response with
        :type   job_id:      int
        :param  response:    the response to save in the DB
        :type   response:    str

        :returns:   the created ChatGXYResponse object
        :rtype:     galaxy.model.ChatGXYResponse

        :raises: InternalServerError
        """
        # TODO: Maybe we need to first check if the job_id exists (in the `job` table)?
        chat_response = ChatGXYResponse(job_id=job_id, response=response)
        trans.sa_session.add(chat_response)
        with transaction(trans.sa_session):
            trans.sa_session.commit()
        return chat_response

    def get(self, trans: ProvidesUserContext, job_id: JobIdPathParam) -> ChatGXYResponse:
        """
        Returns the chat response from the DB based on the given job id.

        :param  job_id:      id of the job to load a response for from the DB
        :type   job_id:      int

        :returns:   the loaded ChatGXYResponse object
        :rtype:     galaxy.model.ChatGXYResponse

        :raises: InconsistentDatabase, InternalServerError
        """
        try:
            stmt = select(ChatGXYResponse).where(ChatGXYResponse.job_id == job_id)
            chat_response = self.session().execute(stmt).scalar_one()
        except MultipleResultsFound:
            # TODO: Unsure about this, isn't this more applicable when we're getting the response for response.id instead of response.job_id?
            raise InconsistentDatabase("Multiple chat responses found with the same job id.")
        except NoResultFound:
            # TODO: Would there be cases where we raise an exception here? Or, is there a better way to return None?
            # raise RequestParameterInvalidException("No accessible response found with the id provided.")
            return None
        except Exception as e:
            raise InternalServerError(f"Error loading from the database.{unicodify(e)}")
        return chat_response

    def set_feedback(self, trans: ProvidesUserContext, job_id: JobIdPathParam, feedback: int) -> ChatGXYResponse:
        """
        Set the feedback for a chat response.

        :param  job_id:      id of the job to associate the feedback with
        :type   job_id:      int
        :param  feedback:    the feedback to save in the DB (0 or 1)
        :type   feedback:    int

        :returns:   the updated ChatGXYResponse object
        :rtype:     galaxy.model.ChatGXYResponse

        :raises: RequestParameterInvalidException
        """

        # Validate the feedback; it should be 0 or 1
        if feedback not in [0, 1]:
            raise RequestParameterInvalidException("Feedback should be 0 or 1.")

        chat_response = self.get(trans, job_id)

        # TODO: Right now, feedback can be changed over and over. If we want to restrict that, we can add a check here.

        chat_response.feedback = feedback

        with transaction(trans.sa_session):
            trans.sa_session.commit()

        return chat_response
