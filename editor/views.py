from django.shortcuts import render,redirect
from .models import *
from django.http import HttpResponse, JsonResponse
from .tasks import run_code_fn , install_package ,run_code_task, stop_container_task
from django.db.models import Count
import docker
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
# client = docker.from_env()

def channel(request,channel_id):
    print('channel is is : ', channel_id)
    channel = Channel.objects.get(id = channel_id)
    
    channels_files = CodeFile.objects.filter(
        channel = channel
    ).order_by('-date')
   
    context={
        'room_name':channel_id,
        'channel':channel,
        'channels_files':channels_files,
        'url':request.build_absolute_uri()
    }
    if request.user.is_authenticated:
        userprofile = UserProfile.objects.get(user = request.user)
        try:
            user_container = UserContainer.objects.get(user=userprofile)

            # Get the Docker container
            # container = client.containers.get(user_container.container_id)
            # container_status = container.status
        except:
            container_status = "You are using Global Container"
        context.update({
            'userprofile':userprofile, 
            'container_status':container_status
            })
    return render (request, 'editor/room2.html',context)
def home(request):
    channels = Channel.objects.all()
    users = UserProfile.objects.all()
    chats = GlobalChatRoom.objects.all()
    
    
    context={
        'channels':channels,
        'users':users,
        'chats':chats
    }

    
    if request.user.is_authenticated:
        userprofile = UserProfile.objects.get(user = request.user)
        try:
            container = UserContainer.objects.get(user=userprofile)
        except:
            container=None
        
        context.update({'userprofile':userprofile, 'container':container})
    return render (request, 'editor/homepage.html',context)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('home')  


from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate input fields
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
        else:
            # Create the user
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            upro =UserProfile.objects.create(user=user)
            upro.save()
            messages.success(request, "Account created successfully! You can now log in.")
            user = authenticate(request, username=username, password=password1)
            if user is not None:
                login(request, user)
            return redirect('login')  # Replace 'login' with the name of your login URL

    return render(request, 'editor/register.html')


@csrf_exempt
def save_file(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        code = data.get('code')
        chnl_id = data.get('channel_id')
        file_id = data.get('file_id',None)
        
        print(data)
        
        if chnl_id and code:
            # Make sure channel_id exists before redirecting
            
            print(code)
            channel = Channel.objects.get(id = chnl_id)
            if file_id != None:
                code_file = CodeFile.objects.get(
                    id = file_id
                )
                code_file.channel = channel
                code_file.file = code
                code_file.file_name = name
                code_file.save()
            else:
                code_file = CodeFile.objects.create(
                    file = code,
                    channel = channel,
                    file_name=name
                )
            
            # return redirect('channel', channel_id=chnl_id)
            return JsonResponse({"msg":"File created"})
        else:
            return JsonResponse({"error":"Channel ID missing or your file has no Code"})
    
    return JsonResponse({"error":"Invalid request method"})



def chat_room(request,user_id):
    
    user1 = UserProfile.objects.get(id =user_id)
    current_user = UserProfile.objects.get(user = request.user)
    
    
    room = (DMRoom.objects
                .filter(participant=user1)
                .filter(participant=current_user)
                # .annotate(num_participants=Count('participant'))
                # .filter(num_participants=2)
                .first()
                )
    print(room)
    if not room:
        room = DMRoom.objects.create()
        room.participant.add(current_user, user1)

    print('Done',room.pk)
    context={
        'current_user':current_user,
        'user1':user1,
        'room':room
        
    }
    return render(request, 'editor/chat.html',context)

def create_channel(request):
    if request.method == "GET":
        name = request.GET.get('name')
        language = request.GET.get('language')
        print(f'Channel Name is : {name}')
        u=request.user
        uprofile = UserProfile.objects.get(user=u)
        channel = Channel.objects.create(name=name,created_by = uprofile,programing_language=language)
        channel.participants.add(uprofile)
        channel.has_permission.add(uprofile)
        return redirect('channel', channel_id = channel.id)
    else: return HttpResponse('Some error occured')
def join_channel(request,channel_id):
    if request.user.is_authenticated and channel_id:
        try:
            channel = Channel.objects.get(
                id = channel_id
            )
        except:
            return HttpResponse('There is No such channel')
        user = request.user
        userprofile = UserProfile.objects.get(user=user)
        all_user = channel.participants.all()
        if user not in all_user:
            channel.participants.add(userprofile)
            channel.save()
        
        return redirect('channel', channel_id=channel_id)
    return HttpResponse('Some error Orrcured')

import os
import subprocess
def create_user_env(base_path, user_id):
    # Create user-specific path
    user_env_path = os.path.join(base_path, f"user_{user_id}")
    os.makedirs(user_env_path, exist_ok=True)

    # Set up a virtual environment if it doesn't exist
    venv_path = os.path.join(user_env_path, "bin", "activate")
    if not os.path.exists(venv_path):
        try:
            subprocess.check_call(["python", "-m", "venv", user_env_path])
        except Exception as e:
            print(e)
    return user_env_path

import json
base_path = "\RCE\packages"
def install_package_view(request):
    if request.method == "POST":
        body = json.loads(request.body)
        package_name = body.get("package")
        print('============================')
        print(package_name)
        print('============================')
        user_id = request.user.id  # Assuming users are authenticated
        user_env_path = create_user_env(base_path, user_id) # Customize per user
        result = install_package(package_name, user_env_path)
        return JsonResponse({ "status": "Processing"})
    
def package_install(request):
    return render(request, 'editor/installpackage.html')

def create_container(request):
    try:
        client = docker.from_env()
        print('container list: ', client.containers.list())
    except Exception as E:
        return HttpResponse(f'Error happend: {E}')
    try:
        user,created =UserProfile.objects.get_or_create(user = request.user)
        
        # code_volume_host = f"
        code_volume_container = "/code_file"
        user_dir_host = os.path.join("./user_code_file", f"user_{user}")
        user_dir_host = os.path.abspath(user_dir_host)
        os.makedirs(user_dir_host, exist_ok=True)
        # Define volumes
        volumes = {
            user_dir_host: {'bind': code_volume_container, 'mode': 'rw'}
        }

        # Run the container
        container = client.containers.run(
            image="realtime_code_editor-ubuntu_env:latest",
            detach=True,
            command="sleep infinity",
            name=f"user_{user.id}_container",
            hostname=f"user_{user.id}",
            volumes=volumes,
            working_dir="/code_file"
        )
        
        UserContainer.objects.create(user=user, container_id=container.id)
        
        stop_container_task.apply_async(
                    args = [container.id],
                    countdown = 20
                )
        return HttpResponse(f'user container created, container id is:{container.id}')
        
    except Exception as e:
        return HttpResponse(e)
    

@csrf_exempt
def start_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code','')
        inputs = data.get('inputs','')
        roomName = data.get('roomName','')
        language = data.get('language','')
        code_executed_by = data.get('code_executed_by','')
        task = run_code_task(code,inputs,code_executed_by,roomName,language)

        return JsonResponse({'task_id': task})
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import docker
import json

@csrf_exempt
def start_container(request):
    if request.method == 'POST':
        context ={}
        try:
            # Parse JSON body
            data = json.loads(request.body)
            user_id = data.get('user_id')

            # Validate user_id
            if not user_id:
                return JsonResponse({'error': 'user_id is required'}, status=400)

            # Initialize Docker client
            client = docker.from_env()

            # Get the user and related container
            userprofile = UserProfile.objects.get(id=user_id)
            user_container = UserContainer.objects.get(user=userprofile)

            # Get the Docker container
            container = client.containers.get(user_container.container_id)
            print('Container status before: ', container.status)

            # Check and start the container if not running
            if container.status != "running":
                container.start()
                print('Container status: ', container.status)
                
                stop_container_task.apply_async(
                    args = [container.id],
                    countdown = 20 *60
                )
                
                

            # Serialize data for response
                userprofile_data = {
                    'username': userprofile.user.username,
                }

                context={
                    'container_status': "Connected",
                    'userId': user_id,
                    'userprofile': userprofile_data,
                    'container_id': user_container.container_id,
                }

            return JsonResponse(context)

        except UserProfile.DoesNotExist:
            return JsonResponse({'error': f'UserProfile with id {user_id} does not exist'}, status=404)

        except UserContainer.DoesNotExist:
            return JsonResponse({'error': f'Container for user {user_id} does not exist'}, status=404)

        except docker.errors.NotFound:
            return JsonResponse({'error': 'Docker container not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


def start_call(request):
    return render(request, 'editor/call.html')

@csrf_exempt
def give_parmision(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        channel_id = data.get('channel_id')
        userprofile = UserProfile.objects.get(id=user_id)
        channel = Channel.objects.get(id=channel_id)
        
        channel.has_permission.add(userprofile)
        
        channel.save()
        
        return JsonResponse({'msg':f'{userprofile} now has permission, Tell him to reload the page','id':user_id})
    else:
        return JsonResponse({'error':'Invalid HTTP method'})
    

def code_template(request):
    return render(request,'editor/code_template.html')
        