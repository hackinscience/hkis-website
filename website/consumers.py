import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer


logger = logging.getLogger(__name__)


class AnswerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.exercise_id = self.scope["url_route"]["kwargs"]["exercise_id"]
        logger.info(
            "WS connect, user: %s, exercise: %s", self.user_id, self.exercise_id
        )
        self.groups = [
            "answers.{}.{}".format(self.user_id, self.exercise_id),
            "snippets.{}".format(self.user_id),
        ]

        for group in self.groups:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(
            "WS disconnect, user: %s, exercise: %s", self.user_id, self.exercise_id
        )
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def correction(self, correction):
        logger.info(
            "WS push correction for user: %s, exercise: %s",
            self.user_id,
            self.exercise_id,
        )
        await self.send_json(correction)

    async def snippet(self, snippet):
        logger.info("WS push snippet for user: %s", self.user_id)
        await self.send_json(snippet)
