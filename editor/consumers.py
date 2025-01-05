import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import run_code_task
from celery.result import AsyncResult
from datetime import datetime
from .models import *
from asgiref.sync import async_to_sync, sync_to_async

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

class GlobalChat(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['url_route']['kwargs']['user']
        self.room_group_name = f'global_chat'

      
        now = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
         
        )
        await self.accept()
        
        await self.channel_layer.group_send( 
            self.room_group_name,
            {
            'type':'send.global',
            "message": f"{user} is connected!",
            'sender':"Admin",
            "time":now 
            } 
            
        )

    async def disconnect(self):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        sender = data.get('sender', '')
        userImage = data.get('userImage', '')
        time = data.get('time', '')
        user_id = data.get('user_id', '')
        from asgiref.sync import sync_to_async

        if user_id:
            try:
                user = await sync_to_async(UserProfile.objects.get)(id=user_id)
                # print('user is:', user.user.username)
            except UserProfile.DoesNotExist:
                print(f'User with id {user_id} does not exist.')
                user = None  # Handle this appropriately based on your logic.

        if user:
            try:
                await sync_to_async(GlobalChatRoom.objects.create)(
                    sender=user,
                    message=message
                )
                print("Message saved successfully!")
            except Exception as e:
                print(f"Error saving message: {e}")

    
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':'send.global',
                'message':message,
                'sender':sender,
                "userImage":userImage,
                "time":time
            }
        )
    async def send_global(self,event):
        message = event.get('message','')
        sender = event.get('sender','')
        userImage = event.get('userImage','https://www.pngplay.com/wp-content/uploads/12/User-Avatar-Profile-PNG-Free-File-Download.png')
        time = event.get('time','')
        
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'userImage': userImage,
            "time":time
        }))


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
