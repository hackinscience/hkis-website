import asyncio
import json
import logging
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils.timezone import now

from hkis.tasks import check_answer
from hkis.models import Answer, Exercise, User, UserInfo
from hkis.utils import markdown_to_bootstrap
from hkis.serializers import AnswerSerializer

logger = logging.getLogger(__name__)

# Channels reminders:
# - The consumer class is instanciated once per websocket connection
#   (once per browser tab), it's the lifespan of a what channels call a scope.
# - Group can group together multiple scopes, usefull to send a
#   message to all browser tabs of a given user at once for example.


@database_sync_to_async
def db_flag_as_unhelpfull(user_id: int, answer_id: int):
    try:
        answer = Answer.objects.get(user_id=user_id, id=answer_id)
    except Answer.DoesNotExist:
        return False
    answer.is_unhelpfull = True
    answer.save()
    return answer


@database_sync_to_async
def db_create_answer(exercise_id: int, user_id: int, source_code):
    answer = Exercise.objects.get(pk=exercise_id).answers.create(
        source_code=source_code, user_id=user_id
    )
    return answer


@database_sync_to_async
def db_get_exercise(exercise_id: int) -> Exercise:
    return Exercise.objects.get(id=exercise_id)


@database_sync_to_async
def db_find_uncorrected(answer_id: int, user: User) -> Optional[dict]:
    try:
        answer = Answer.objects.get(id=answer_id, user=user, is_corrected=False)
        return {
            "check": answer.exercise.check,
            "pre_check": answer.exercise.pre_check,
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
    rank = None
    if answer.is_valid and answer.user_id:
        userinfo, _ = UserInfo.objects.get_or_create(user=answer.user)
        rank = userinfo.recompute_rank()
        for team in answer.user.teams.all():
            team.recompute_rank()
    return answer, rank


def answer_message(answer: Answer, rank: int = None) -> dict:
    message = AnswerSerializer(answer).data
    if rank:
        message["user_rank"] = rank
    message["correction_message_html"] = markdown_to_bootstrap(
        message["correction_message"]
    )
    message["type"] = "answer.update"
    return message


def log(message, *args):
    if args:
        message = message + ": " + str(args)
    logger.info("WebSocket %s", message)


class ExerciseConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.settings = {}
        self.exercise: Optional[Exercise] = None
        super().__init__(*args, **kwargs)

    async def connect(self):
        log("connect")
        self.exercise = await db_get_exercise(
            self.scope["url_route"]["kwargs"]["exercise_id"]
        )
        log("accept")
        await self.accept()

    async def disconnect(self, code):
        logger.info("WebSocket disconnect (code=%s)", code)

    async def receive_json(self, content, **kwargs):
        if content["type"] == "answer":
            asyncio.create_task(self.answer(content["source_code"]))
        elif content["type"] == "is_unhelpfull":
            asyncio.create_task(self.flag_as_unhelpfull(content["answer_id"]))
        elif content["type"] == "recorrect":
            asyncio.create_task(self.recorrect(content))
        elif content["type"] == "settings":
            self.settings = content["value"]
        else:
            log("Unknown message received", json.dumps(content))

    async def flag_as_unhelpfull(self, answer_id: str):
        try:
            answer_id_int = int(answer_id)
        except ValueError:
            return
        answer = await db_flag_as_unhelpfull(self.scope["user"].id, answer_id_int)
        if answer:
            await self.send_json(answer_message(answer))

    async def recorrect(self, answer):
        log("Restarting correction for an answer")
        uncorrected = await db_find_uncorrected(answer["id"], self.scope["user"])
        if not uncorrected:
            return
        log("Send answer to moulinette")
        is_valid, message = await check_answer(
            {
                "check": uncorrected["check"],
                "pre_check": uncorrected["pre_check"],
                "source_code": uncorrected["source_code"],
                "language": self.settings.get("LANGUAGE_CODE", "en"),
            }
        )
        log("Got result from moulinette")
        answer, rank = await db_update_answer(uncorrected["id"], is_valid, message)
        await self.send_json(answer_message(answer, rank))

    async def answer(self, source_code):
        log("Receive answer from browser")
        answer = await db_create_answer(
            self.exercise.id, self.scope["user"].id, source_code
        )
        await self.send_json(answer_message(answer))
        log("Send answer to moulinette")
        is_valid, message = await check_answer(
            {
                "check": answer.exercise.check,
                "pre_check": answer.exercise.pre_check,
                "source_code": source_code,
                "language": self.settings.get("LANGUAGE_CODE", "en"),
            }
        )
        log("Got result from moulinette")
        answer, rank = await db_update_answer(answer.id, is_valid, message)
        await self.send_json(answer_message(answer, rank))
