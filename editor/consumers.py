import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import run_code_task
from celery.result import AsyncResult

class CodeEditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'editor_{self.room_name}'

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

        if 'code' in text_data_json:
            code = text_data_json['code']
            code_executed_by = text_data_json['code_executed_by']
            # coding_by = text_data_json.get('coding_by','')

            # Execute the code using Celery and get the task ID
            task = run_code_task.delay(code)
            
            task_id = task.id
            
            print('Task id ::::::',task)

            # Send the task ID back to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_code_output',
                    'message': 'Processing...',
                    'code_executed_by': code_executed_by,
                    'raw_code': code,
                    'task_id': task_id,
                    # 'coding_by':coding_by
                }
            )

        elif 'task_id' in text_data_json:
            # Client is checking the task status
            task_id = text_data_json['task_id']
            
            print('task is : ',task_id)

            if task_id:  # Check if task_id is valid
                task = AsyncResult(task_id)

                if task.ready():
                    output = task.result 
                else:
                    output = 'Processing...' 

                
                await self.send(text_data=json.dumps({
                    'message': output,
                    'task_id': task_id
                }))
            else:
                # Handle case where task_id is None or invalid
                await self.send(text_data=json.dumps({
                    'message': 'Invalid task ID provided.',
                    'task_id': task_id
                }))

        elif 'raw_code' in text_data_json:
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
        task_id = event.get('task_id')
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
