import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import run_code_task
from celery.result import AsyncResult

class CodeEditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'editor_{self.room_name}'

        print('===================================')
        print('----------For editor------------')
        print(f'={self.channel_name}=')
        print(f'={self.channel_layer}')
        print(f'={self.room_group_name}')
        print('===================================')
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Parse the incoming data
        text_data_json = json.loads(text_data)
        
        print('Text Data Json: ====', text_data_json)

 
        if 'raw_code' in text_data_json:
            raw_code = text_data_json['raw_code']
            coding_by = text_data_json.get('coding_by','')

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_code_output',
                    'raw_code': raw_code,
                    'message': '',
                    'coding_by':coding_by
                }
            )


    # Broadcast the code or its output to all connected clients in the group
    async def send_code_output(self, event):
        message = event['message']
        raw_code = event.get('raw_code', '')
        code_executed_by = event.get('code_executed_by', '')
        task_id = event.get('task_id','')
        coding_by = event.get('coding_by','')

       
        if task_id:
            task = AsyncResult(task_id)
            if task.ready():
                message = task.result  
            else:
                message = 'Processing...'  # Keep informing that it's processing
                
        print(message)


        await self.send(text_data=json.dumps({
            'message': message,  # The output of the code execution
            'raw_code': raw_code,
            'code_executed_by': code_executed_by,
            'task_id':task_id,
            'coding_by':coding_by
        }))


class TaskResult(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'task_{self.room_name}'
        print('connected')
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    async def disconnect(self):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    
    async def task_update(self, event):
        
        print('happend')
        await self.send(text_data=json.dumps({
            "output": event["output"],
            "code_executed_by": event["code_executed_by"],
        }))

    
    
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chat_room']
        self.room_group_name = f'chat_{self.room_name}'
        
        print('===================================')
        print('----------For Chat------------')
        print(f'={self.channel_name}=')
        print(f'={self.channel_layer}')
        print(f'={self.room_group_name}')
        print('===================================')
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
         
        )
        await self.accept()
    
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        print(text_data_json)
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_data',
                    'data':text_data_json
                }
            )
        # await self.send(
        #     json.dumps(text_data_json)
        # )
        
    async def send_data(self,event):
        data = event.get('data')
        await self.send(text_data=json.dumps(
            data
        ))
    

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_group_name = f'user_{self.scope["user"].id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'notification': event['notification']
        }))
