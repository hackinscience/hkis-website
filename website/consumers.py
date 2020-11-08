import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User
from django.utils.timezone import now

from moulinette.tasks import check_answer, run_snippet
from website.models import Answer, Exercise, Snippet, UserStats
from website.utils import markdown_to_bootstrap
from website.serializers import AnswerSerializer, SnippetSerializer

logger = logging.getLogger(__name__)

# Channels reminders:
# - The consumer class is instanciated once per websocket connection
#   (once per browser tab), it's the lifespan of a what channels call a scope.
# - Group can group together multiple scopes, usefull to send a
#   message to all browser tabs of a given user at once for example.


@database_sync_to_async
def db_store_correction(answer, is_valid, message):
    answer = Answer.get(answer["id"])
    answer.is_valid = is_valid
    answer.correction_message = message
    answer.save()


@database_sync_to_async
def db_create_answer(exercise_id: int, user_id: int, source_code):
    answer = Exercise.objects.get(pk=exercise_id).answers.create(
        source_code=source_code, user_id=user_id
    )
    return answer


@database_sync_to_async
def db_create_snippet(user: User, source_code):
    return Snippet.objects.create(
        source_code=source_code, user=user if not user.is_anonymous else None
    )


@database_sync_to_async
def db_get_exercise(exercise_id: int):
    return Exercise.objects.get(id=exercise_id)


@database_sync_to_async
def db_find_uncorrected(answer_id: int, user: User) -> dict:
    try:
        answer = Answer.objects.get(id=answer_id, user=user, is_corrected=False)
        return {
            "check": answer.exercise.check,
            "source_code": answer.source_code,
            "id": answer.id,
        }
    except Answer.DoesNotExist:
        return None


@database_sync_to_async
def db_update_answer(answer_id: int, is_valid: bool, correction_message: str):
    answer = Answer.objects.get(id=answer_id)
    answer.correction_message = correction_message
    answer.is_corrected = True
    answer.is_valid = is_valid
    answer.corrected_at = now()
    answer.save()
    if answer.is_valid and answer.user_id:
        user_stats, _ = UserStats.objects.get_or_create(user=answer.user)
        user_stats.recompute()
        rank = user_stats.rank
    else:
        rank = None
    return answer, rank


@database_sync_to_async
def db_update_snippet(snippet_id: int, output: str):
    snippet = Snippet.objects.get(id=snippet_id)
    snippet.output = output
    snippet.executed_at = now()
    snippet.save()
    return snippet


def answer_message(answer: Answer, rank: int = None) -> dict:
    message = AnswerSerializer(answer).data
    if rank:
        message["user_rank"] = rank
    message["correction_message_html"] = markdown_to_bootstrap(
        message["correction_message"]
    )
    message["type"] = "answer.update"
    return message


def snippet_message(snippet: Snippet):
    message = SnippetSerializer(snippet).data
    message["type"] = "snippet.update"
    return message


class ExerciseConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.settings = {}
        super().__init__(*args, **kwargs)

    def log(self, message, *args):
        if args:
            message = message + ": " + str(args)
        logger.info("WebSocket %s", message)

    async def connect(self):
        self.log("connect")
        self.exercise = await db_get_exercise(
            self.scope["url_route"]["kwargs"]["exercise_id"]
        )
        self.log("accept")
        await self.accept()

    async def disconnect(self, close_code):
        self.log("disconnect")

    async def receive_json(self, content):
        if content["type"] == "answer":
            asyncio.create_task(self.answer(content["source_code"]))
        elif content["type"] == "recorrect":
            asyncio.create_task(self.recorrect(content))
        elif content["type"] == "snippet":
            asyncio.create_task(self.snippet(content))
        elif content["type"] == "settings":
            self.settings = content["value"]
        else:
            self.log("Unknown message received", json.dumps(content))

    async def recorrect(self, answer):
        self.log("Restarting correction for an answer")
        uncorrected = await db_find_uncorrected(answer["id"], self.scope["user"])
        if not uncorrected:
            return
        self.log("Send answer to moulinette")
        is_valid, message = await check_answer(
            {"check": uncorrected["check"], "source_code": uncorrected["source_code"]}
        )
        self.log("Got result from moulinette")
        await db_update_answer(uncorrected["id"], is_valid, message)

    async def answer(self, source_code):
        self.log("Receive answer from browser")
        answer = await db_create_answer(
            self.exercise.id, self.scope["user"].id, source_code
        )
        await self.send_json(answer_message(answer))
        self.log("Send answer to moulinette")
        is_valid, message = await check_answer(
            {
                "check": answer.exercise.check,
                "source_code": source_code,
                "language": self.settings.get("LANGUAGE_CODE", "en"),
            }
        )
        self.log("Got result from moulinette")
        answer, rank = await db_update_answer(answer.id, is_valid, message)
        message = AnswerSerializer(answer).data
        if rank:
            message["user_rank"] = rank
        message["correction_message_html"] = markdown_to_bootstrap(
            message["correction_message"]
        )
        message["type"] = "answer.update"
        await self.send_json(message)

    async def snippet(self, snippet):
        """Snippet runner does not listen for DB events: it awaits for the
        snippet to run and send the result to the caller, no channels
        group involved (it won't be sent to other browser tabs).

        Note it's a distinct task (started by receive_json) to avoid
        blocking this consumer.
        """
        self.log("Receive snippet from browser")
        snippet_obj = await db_create_snippet(
            self.scope["user"], snippet["source_code"]
        )
        message = SnippetSerializer(snippet_obj).data
        message["type"] = "snippet.update"
        await self.send_json(message)
        self.log("Sending snippet to runner")
        result = await run_snippet(snippet["source_code"])
        self.log("Got result from snippet runner")
        snippet_obj = await db_update_snippet(snippet_obj.id, result)
        message = SnippetSerializer(snippet_obj).data
        message["type"] = "snippet.update"
        await self.send_json(message)
