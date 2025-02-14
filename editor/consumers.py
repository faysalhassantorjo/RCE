import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import run_code_task
from celery.result import AsyncResult
from datetime import datetime
from .models import *
from asgiref.sync import async_to_sync, sync_to_async
import redis

# Replace with your Redis URL
redis_client = redis.Redis.from_url("redis://red-cuj40v0gph6c73fqc0ig:6379/0")


# redis_client = redis.StrictRedis(host='redis_server', port=6379,db=0)
# redis_client = redis.StrictRedis(host='127.0.0.1', port=6379,db=0)


try:
    print('redis_client_response',redis_client.ping())  # Should return True if connected
except Exception as e:
    print(f"Error: {e}")


class CodeEditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        userprofile_id = self.scope['url_route']['kwargs']['userprofile']
        self.room_group_name = f'editor_{self.room_name}'

        userprofile = await sync_to_async(UserProfile.objects.get)(id=userprofile_id)
        username = await sync_to_async(lambda: userprofile.user.username)()
        userimage = await sync_to_async(lambda: userprofile.imageURL())()


        user_data = {
            "username": username,
            "image": userimage,
        }

        stored_data = redis_client.get(self.room_group_name)

        if stored_data:
            all_users = list(json.loads(stored_data))
        else:
            all_users = []

        if user_data in all_users:
            pass
        else:
            all_users.append(user_data)

        serialized_user_data = json.dumps(all_users)
        redis_client.set(self.room_group_name, serialized_user_data)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':'allconnecteduser'
            }
        )
    async def allconnecteduser(self,event):
        
        all_users = redis_client.get(self.room_group_name)
        if all_users:
            all_users = json.loads(all_users)
            print("All Connected Users:")
            print(all_users)

        await self.send(text_data=json.dumps({
            'connected_users': all_users,
        }))
        

    async def disconnect(self, close_code):
        print('Disconnecting with close code:', close_code)
        await self.handle_user_leave()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def handle_user_leave(self):
        print('Sending leave_user event to group:', self.room_group_name)
        all_users = redis_client.get(self.room_group_name)
        if all_users:
            all_users = list(json.loads(all_users))
        userprofile_id = self.scope['url_route']['kwargs']['userprofile']

        userprofile = await sync_to_async(UserProfile.objects.get)(id=userprofile_id)
        username = await sync_to_async(lambda: userprofile.user.username)()
        userimage = await sync_to_async(lambda: userprofile.imageURL())()


        # Prepare user data
        user_data = {
            "username": username,
            "image": userimage,
        }  
        
        if user_data in all_users:
            all_users.remove(user_data)
        
        print('After user disconnected: all data is : ', json.dumps(all_users)) 
        redis_client.set(self.room_group_name, json.dumps(all_users))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'leave_user',
                'left_user': username
            }
        )

    async def leave_user(self, event):
        print('leave_user handler called.')

        

        left_user = event.get('left_user')

        await self.send(text_data=json.dumps({
            'left_user': left_user,
            'type':'user_disconnected'
        }))


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        print('Text Data Json: ====', text_data_json)

        # if 'raw_code' in text_data_json:
        #     raw_code = text_data_json['raw_code']
        #     coding_by = text_data_json.get('coding_by','')
        #     user_image = text_data_json.get('user_image','')

        #     await self.channel_layer.group_send(
        #         self.room_group_name,
        #         {
        #             'type': 'send_code_output',
        #             'raw_code': raw_code,
        #             'coding_by':coding_by,
        #             'user_image':user_image,
        #             'text_data_json':text_data_json
        #         }
        #     )
            
        if text_data_json.get('type') == 'code_change':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_code_change',
                    'changes': text_data_json['changes'],
                    'coding_by': text_data_json['coding_by'],
                    'user_image': text_data_json['user_image']
                }
            )

    async def broadcast_code_change(self, event):
        await self.send(text_data=json.dumps({
            'type': 'code_change',
            'changes': event['changes'],
            'coding_by': event['coding_by'],
            'user_image': event['user_image']
        }))


    # Broadcast the code or its output to all connected clients in the group
    async def send_code_output(self, event):
        raw_code = event.get('raw_code', '')
        coding_by = event.get('coding_by','')
        user_image = event.get('user_image','')
        text_data_json = event.get('text_data_json','')
        

       
     


        await self.send(text_data=json.dumps({
            'raw_code': raw_code,
            'coding_by':coding_by,
            'user_image':user_image,
            'text_data_json':text_data_json,
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
    async def disconnect(self, code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    
    async def task_update(self, event):
        

        output = event.get('output')
        code_executed_by = event.get('code_executed_by')
        
        print('Output is: ', output)
        
        await self.send(text_data=json.dumps({
            "output": output,
            "code_executed_by": code_executed_by,
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

    async def disconnect(self, close_code):
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



class PermissionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'permission_room_{self.channel_id}'
        print('Permission Room Connected!')
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data=None):
        data = json.loads(text_data)
        
        username = data.get('user_name')
        user_id = data.get('user_id')
        type = data.get('type')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':'handle_permission',
                'user':username,
                'user_id':user_id,
                'permission_type':type
            }
        )        
    async def handle_permission(self,event):
        user = event.get('user')
        user_id = event.get('user_id')
        permission_type = event.get('permission_type')
        
        userpro = await sync_to_async(UserProfile.objects.get)(id=user_id)
        channel = await sync_to_async(Channel.objects.get)(id =self.channel_id)
        
        if permission_type == "remove":
            await sync_to_async(channel.has_permission.remove)(userpro)
        else:
            await sync_to_async(channel.has_permission.add)(userpro)
        
        
        
        await self.send(text_data=json.dumps({
            'user': user,
            'user_id': user_id,
            'type':permission_type
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







class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"Path: {self.scope['path']}")
        print(f"Room Name: {self.scope['url_route']['kwargs']['room_name']}")
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'

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
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_message',
                'message': data
            }
        )

    async def call_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))






class OTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = "global_document"  # Single document for simplicity
        self.group_name = f"document_{self.document_id}"

        # Join the document's group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Send the current document state to the new client
        content = await self.get_document_content()
        print('Initial document content:', content)

        await self.send(text_data=json.dumps({
            'type': 'update',
            'content': content,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        operation = data['operation']
        print('Received operation:', operation)

        # Apply the operation to the document
        content = await self.apply_operation(operation)

        # Broadcast the updated content to all clients
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_update',
                'operation': operation,  # Send only the delta update
            }
        )

    async def send_update(self, event):
        operation = event['operation']

        # Exclude the sender by checking the channel name
        if self.channel_name != event.get('sender_channel'):
            await self.send(text_data=json.dumps({
                'type': 'update',
                'operation': operation
            }))

    @sync_to_async
    def get_document_content(self):
        # Retrieve the document content from Redis and decode it to a string
        content = redis_client.get("document_content")
        return content.decode('utf-8') if content else ""

    @sync_to_async
    def apply_operation(self, operation):
        """
        Apply an insert or delete operation to the document content stored in Redis.
        """
        # Validate the operation
        if not self._is_valid_operation(operation):
            raise ValueError("Invalid operation format")

        # Retrieve the document content from Redis and decode it to a string
        content = redis_client.get("document_content")
        content = content.decode('utf-8') if content else ""
        lines = content.split('\n')

        # Extract position and type
        position = operation['position']
        line = position['line']
        ch = position['ch']

        if operation['type'] == 'insert':
            lines = self._apply_insert(lines, line, ch, operation['text'])
        elif operation['type'] == 'delete':
            lines = self._apply_delete(lines, line, ch, operation['length'])

        # Reconstruct the document content
        updated_content = '\n'.join(lines)

        # Save the updated content back to Redis (encode string to bytes)
        redis_client.set("document_content", updated_content.encode('utf-8'))

        return updated_content

    def _is_valid_operation(self, operation):
        """
        Validate the structure of the operation object.
        """
        required_fields = {'type', 'position'}
        if operation['type'] == 'insert':
            required_fields.add('text')
        elif operation['type'] == 'delete':
            required_fields.add('length')
        return all(field in operation for field in required_fields)

    def _apply_insert(self, lines, line, ch, text):
        """
        Apply an insert operation to the document lines.
        """
        if line >= len(lines):
            # Extend the list of lines if the target line doesn't exist
            lines.extend([''] * (line - len(lines) + 1))
        lines[line] = lines[line][:ch] + text + lines[line][ch:]
        return lines

    def _apply_delete(self, lines, line, ch, length):
        """
        Apply a delete operation to the document lines.
        """
        remaining_length = length
        current_line = line

        while remaining_length > 0 and current_line < len(lines):
            line_length = len(lines[current_line])
            chars_to_remove = min(remaining_length, line_length - ch)

            if chars_to_remove > 0:
                lines[current_line] = (
                    lines[current_line][:ch] +
                    lines[current_line][ch + chars_to_remove:]
                )
                remaining_length -= chars_to_remove

            ch = 0  # Reset character index for subsequent lines
            current_line += 1

        return lines