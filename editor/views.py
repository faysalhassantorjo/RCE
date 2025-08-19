from django.shortcuts import render,redirect
from .models import *
from django.http import HttpResponse, JsonResponse
from .tasks import run_code_fn , install_package ,run_code_task, stop_container_task
from django.db.models import Count
import docker
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

# Create your views here.
client = docker.from_env()

def channel(request,channel_id):
    channel = Channel.objects.get(id = channel_id)
    
    channels_files = CodeFile.objects.filter(
        channel = channel
    ).order_by('-date')
    
    try:
        lab_test = LabTest.objects.get(channel_id =channel_id, available=True)
    except:
        lab_test =[]
   
    context={
        'room_name':channel_id,
        'channel':channel,
        'channels_files':channels_files,
        'url':request.build_absolute_uri(),
        'lab_test':lab_test
    }
    if request.user.is_authenticated:
        userprofile = UserProfile.objects.get(user = request.user)
        container = None
        try:
            user_container = UserContainer.objects.get(user=userprofile)
            container = client.containers.get(user_container.container_id)
            container_status = container.status
        except:
            container_status = None
        context.update({
            'userprofile':userprofile, 
            'container_status':container_status,
            'container':container,
            })
    return render (request, 'editor/room2.html',context)

@login_required(login_url='/login/')
def home(request):
    users = UserProfile.objects.all()
    user = request.user
    channels = Channel.objects.filter(participants__user = user).order_by('-id')
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
    if request.method == "POST":
        name = request.POST.get('name')
        language = request.POST.get('language')
        picture = request.FILES.get('channel_picture')

        u = request.user
        uprofile = UserProfile.objects.get(user=u)

        channel = Channel.objects.create(
            name=name,
            created_by=uprofile,
            programing_language=language,
            channel_picture=picture if picture else 'profile_pictures/default.jpg'
        )
        channel.participants.add(uprofile)
        channel.has_permission.add(uprofile)

        return redirect('channel', channel_id=channel.id)

    return HttpResponse('Invalid request method', status=400)

    
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
        user =UserProfile.objects.get(user = request.user)
        
        
        # Run the container
        container = client.containers.run(
            image="realtime_code_editor-environment:latest",
            detach=True,
            command="sleep infinity",
            name=f"user_{user.id}_container",
            hostname=f"user_{user.id}",
            working_dir="/code_file"  # Optional, just for consistency
        )
        
        exit_code, output = container.exec_run("pip freeze")
        installed_packages=""
        if exit_code == 0:
            installed_packages = output.decode("utf-8")
            print(installed_packages)
        else:
            print("Something went wrong.")
                
        
        
        UserContainer.objects.create(user=user, container_id=container.id, installed_packages= installed_packages)
        
        # stop_container_task.apply_async(
        #             args = [container.id],
        #             countdown = 20
        # )
        return HttpResponse(f'user container created, container id is:{container.id}')
        
    except Exception as e:
        return HttpResponse(e)
    
@login_required
def delete_container(request):
    user_profile = request.user.userprofile
    try:
        user_container = user_profile.usercontainer
    except UserContainer.DoesNotExist:
        user_container = None

    if user_container:
        try:
            container = client.containers.get(user_container.container_id)
            container.stop()
            # Remove it
            container.remove()
        except docker.errors.NotFound:
            print("Container not found in Docker, only deleting DB entry.")

        # Delete the DB record
        user_container.delete()

    return redirect('profile',user_profile.user.id)
    

@csrf_exempt
def start_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code','')
        inputs = data.get('inputs','')
        roomName = data.get('roomName','')
        language = data.get('language','')
        code_executed_by = data.get('code_executed_by','')
        

        task = run_code_task.delay(code,inputs,code_executed_by,roomName,language)

        return JsonResponse({'task_id': task.id, 'status': 'Task started successfully'})
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
                
                userprofile_data = {
                    'username': userprofile.user.username,
                }

                context={
                    'container_status': "running",
                    'userId': user_id,
                    'userprofile': userprofile_data,
                    'container_id': user_container.container_id,
                    'status':'success' ,
                    'auto_stop_in':20
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


from .lexical_analysis import main
@csrf_exempt
def lexical_analysis(request):
    if request.method =='POST':
        data = json.loads(request.body)
        # print(data)
        code = data.get('code','')
        tokens = main(code)
        serialized_tokens = []
        for token in tokens:
            serialized_tokens.append({
                'type': token.type,
                'value': str(token.value) if token.value is not None else None,
                'line': token.line,
                'column': token.column
            })
            
        return JsonResponse({
            'success': True,
            'tokens': serialized_tokens,
            'count': len(serialized_tokens)
        })
    return JsonResponse({'analyzed_data':"analyzed_data"})
    
@csrf_exempt
def create_file(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print('data',data)
        try:
            file = CodeFile.objects.create(
                file_name = data.get('file_name','new_file'),
                channel_id = data.get('channel_id'),
                user_id = data.get('user_id')
            )
            imageURL = file.user.imageURL()
            print(imageURL)
            return JsonResponse({'success':'Yes','id':file.id, 'user_image':imageURL})
        except Exception as e:
            print(e)
            return JsonResponse({'error':'Something went worng'})
        
    return JsonResponse({'success':'no'})

def profile(request, pk):
    
    user_profile = UserProfile.objects.get(user_id = pk)
    container = UserContainer.objects.filter(user=user_profile).first()
    
    context ={
        'user_profile':user_profile,
        'container':container
    }
        
    if container:
        container = client.containers.get(container.container_id)
        status= container.status
        context.update({'status':status})
    
    return render(request, 'editor/profile.html',context)


def test_monitor(request,pk):
    
    
     
    labtest = LabTest.objects.filter(channel_id= pk).first()
    
    all_candidates = AttemptTest.objects.filter(test=labtest)
    
    context={
        'room_id':pk,
        'labtest':labtest,
        'all_candidates':all_candidates
    }
    return render(request, 'editor/test_monitor.html',context)

from datetime import datetime, time
from .tasks import finish_lab_test
import pytz

def send_to_queue_for_stop_test(obj_id,end_at_time):
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    
    # Get current time in Dhaka timezone
    now = datetime.now(dhaka_tz)
    
    # Create exam end time in Dhaka timezone
    exam_end = datetime.combine(now.date(), end_at_time)
    exam_end = dhaka_tz.localize(exam_end)
    
    # If end time has passed today, assume it's tomorrow
    if exam_end <= now:
        from datetime import timedelta
        exam_end += timedelta(days=1)
    
    time_diff = exam_end - now
    total_minute = round(time_diff.total_seconds() / 60, 1)
    
    print(f"Current time (Dhaka): {now.strftime('%H:%M:%S')}")
    print(f"Exam ends at (Dhaka): {exam_end.strftime('%H:%M:%S')}")
    print(f"Total time remaining (minutes): {total_minute}")
    
    # Calculate countdown in seconds for Celery
    countdown_seconds = int(time_diff.total_seconds())
    
    finish_lab_test.apply_async(
        args=[obj_id],
        countdown=countdown_seconds
    )
    

@csrf_exempt
def manage_lab_test(request):
    
    if request.method == "POST":
        try:
            
            room_id = request.POST.get('room_id')
            # question = request.FILES.get('question')
            text_question = request.POST.get('text-question')
            raw_ques = request.POST.get('raw_ques')
            duration = request.POST.get('duration')
            end_at = request.POST.get('end_at')
            title = request.POST.get('title')
            
            end_at_time = datetime.strptime(end_at, "%H:%M").time()
            
            obj, created = LabTest.objects.get_or_create(channel_id = room_id)
            current_time = datetime.now().time()
            # obj.image_question= question
            obj.text_question = text_question
            obj.raw_question_text = raw_ques
            obj.title = title
            obj.duration = duration
            obj.available = True
            obj.created_at = timezone.now()
            obj.end_at = end_at_time
            obj.start_at = current_time
            obj.save()
            
            send_to_queue_for_stop_test(obj.id, end_at_time)
            
        
            
            return JsonResponse({'status':'success'})
        except Exception as e:
            print(e)
            return JsonResponse({'status':'som eerror'})
    return JsonResponse({'status':'invalid request'})

@csrf_exempt
def finish_test(request):
    if request.method == "POST":
        room_id = request.POST.get('room_id')
        obj = LabTest.objects.get(channel_id = room_id)
        AttemptTest.objects.filter(test=obj).delete()
        obj.delete()
        return JsonResponse({'status':'success','room_id':room_id})
    else:
        return JsonResponse({'status':'invalid request'})
        
       


def test_editor(request,pk):
    context ={}
    try:
        lab_test = LabTest.objects.get(id = pk,available=True)
        
        attempt,created = AttemptTest.objects.get_or_create(
            test = lab_test,
            user = request.user
        )

        context.update({
        'room_id':lab_test.channel.id,
        'lab_test':lab_test,
        "room":lab_test.channel,
        "attempt":attempt
        })
    except Exception as e:
        print(e)
        lab_test = None
  
    return render(request, 'editor/test-editor.html',context)



@csrf_exempt 
def save_typing_statistic(request):
    if request.method == 'POST':
        data = json.loads(request.body)        
        user_id = data.get('user')
        room_id = data.get('room_id')
        code_content = data.get('code_content')
        char_deltas = data.get('charDeltas', [])
        time_labels = data.get('timeLabels', [])
        
        print(data)
        
        user= User.objects.get(id=user_id)
        obj = LabTest.objects.get(channel_id = room_id)

        attempt, created = AttemptTest.objects.get_or_create(
            test = obj,
            user=user,
        )
        attempt.code = code_content
        attempt.char_deltas=char_deltas
        attempt.time_labels=time_labels
        attempt.done=True
        attempt.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt  
def get_typing_statistic(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Example: Get user from session (or use request.user if authenticated)
        
        user_id = data.get('user')
        room_id = data.get('room_id')
    
        
        print(data)
        
        user= User.objects.get(id=user_id)
        obj = LabTest.objects.get(channel_id = room_id)

        ateemptobj = AttemptTest.objects.get(
            test = obj,
            user=user, 
        )
        
        char_deltas=ateemptobj.char_deltas,
        time_labels=ateemptobj.time_labels

        return JsonResponse({'status': 'success','char_deltas':char_deltas,'time_labels':time_labels})
    return JsonResponse({'error': 'Invalid method'}, status=405)

def labtest_list(request):
    
    channels = Channel.objects.filter(
        participants__user = request.user
    )
    all_labtest = []
    for channel in channels:
        try:
            labtest = channel.labtest
            all_labtest.append(labtest)
        except Exception as e:
            print(e)
            pass
        
    context ={
        'all_labtest':all_labtest
    }
    print(all_labtest)
    return render(request, 'editor/labtest_list.html',context)

from dotenv import load_dotenv
from langchain_core.prompts import load_prompt
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
import re

load_dotenv()

# Load your prompt once (globally)
template = load_prompt('rce_prompt.json')

# Setup your LLM
llm = HuggingFaceEndpoint(
    model="openai/gpt-oss-120b",
    # model="Qwen/Qwen3-30B-A3B",
    task="text-generation",
)
chat_model = ChatHuggingFace(llm=llm)

import markdown
from django.utils.safestring import mark_safe
from langchain_core.output_parsers import StrOutputParser
parser = StrOutputParser()
def ai_analyse_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        candidate_id = data.get('candidate_id')
        candidate = AttemptTest.objects.get(id=candidate_id)
        labtest = candidate.test
        code = candidate.code
        question = labtest.raw_question_text      

        if candidate.ai_response:
            return JsonResponse({'status': 'success','summary':candidate.ai_response})
        
        chain = template | chat_model | parser

        response = chain.invoke({
            'question': question,
            'code': code
        })
        candidate.ai_response = response
        candidate.save()

        # response_markdown = markdown.markdown(response)

        return JsonResponse({'status': 'success','summary':response})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def catch_pasted_code(request):
    if request.method =='POST':
        data = json.loads(request.body)
        startLine = data.get('startLine')
        endLine = data.get('endLine')
        pastedContent = data.get('pastedContent')
        attempt_id = data.get('attempt_id')
        
        attempt = AttemptTest.objects.get(id=attempt_id)
        
        AttemptPaste.objects.create(
            attempt_test = attempt,
            start_line = startLine,
            end_line = endLine,
            content = pastedContent
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def get_pasted_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        attempt = AttemptTest.objects.get(id=attempt_id)
        pasted_code = AttemptPaste.objects.filter(attempt_test=attempt)
        
        pasted_code_list = []
        for code in pasted_code:
            pasted_code_list.append({
                'id': code.id,
                'start_line': code.start_line,
                'end_line': code.end_line,
                'content': code.content
            })
        
        return JsonResponse({'status': 'success','pasted_code':pasted_code_list})     
           
    return JsonResponse({'error': 'Invalid method'}, status=405)


def view_available_lab(request):
    
    channels = Channel.objects.filter(created_by__user = request.user)
    print(channels)
    
    context ={
        'channels':channels
    }    
    return render(request,'editor/view_available_lab.html',context)

def view_availabe_lab_test(request,channel_id):
    labtests = LabTest.objects.filter(channel_id= channel_id)
    
    context= {
        'labtests':labtests
    }
    
    return render(request, 'editor/test_list.html',context)





