from channels.generic.websocket import AsyncJsonWebsocketConsumer


class AnswerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.exercise_id = self.scope["url_route"]["kwargs"]["exercise_id"]
        self.groups = [
            "answers.{}.{}".format(self.user_id, self.exercise_id),
            "snippets.{}".format(self.user_id),
        ]

        for group in self.groups:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def correction(self, correction):
        await self.send_json(correction)

    async def snippet(self, snippet):
        await self.send_json(snippet)
