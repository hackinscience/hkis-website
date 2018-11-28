from channels.generic.websocket import AsyncJsonWebsocketConsumer


class AnswerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.exercise_id = self.scope["url_route"]["kwargs"]["exercise_id"]
        self.group_name = "answers.{}.{}".format(self.user_id, self.exercise_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def correction(self, correction):
        await self.send_json(correction)
