from django.shortcuts import render,redirect
from .models import *
from django.http import HttpResponse
from .tasks import run_code_fn
from django.db.models import Count
# Create your views here.

def channel(request,channel_id):
    
    channel = Channel.objects.get(id = channel_id)
    
    channels_files = CodeFile.objects.filter(
        channel = channel
    ).order_by('-date')
   
    context={
        'room_name':channel_id,
        'channel':channel,
        'channels_files':channels_files
    }
    return render (request, 'editor/room.html',context)
def home(request):
    channels = Channel.objects.all()
    users = UserProfile.objects.all()
    context={
        'channels':channels,
        'users':users
    }
    if request.method == 'POST':
        code = request.POST.get('code')
        # chnl_id = request.POST.get('channel_id')
        # file_id = request.POST.get('file_id',None)
        # print('file id is: ',file_id)
        result = run_code_fn(code)
        
        context.update({
            'result':result
        })
   
    
    if request.user.is_authenticated:
        userprofile = UserProfile.objects.get(user = request.user)
        context.update({'userprofile':userprofile})
    return render (request, 'editor/homepage.html',context)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('home')  

def save_file(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        chnl_id = request.POST.get('channel_id')
        file_id = request.POST.get('file_id',None)
        print('file id is: ',file_id)
        
        if chnl_id and code:
            # Make sure channel_id exists before redirecting
            
            print(code)
            channel = Channel.objects.get(id = chnl_id)
            if file_id != 'undefined':
                code_file = CodeFile.objects.get(
                    id = file_id
                )
                code_file.channel = channel
                code_file.file = code
                code_file.save()
            else:
                code_file = CodeFile.objects.create(
                    file = code,
                    channel = channel
                )
            
            return redirect('channel', channel_id=chnl_id)
        else:
            return HttpResponse("Channel ID missing your file has no Code", status=400)
    
    return HttpResponse("Invalid request method", status=405)



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
        print(f'Channel Name is : {name}')
        channel = Channel.objects.create(name=name,created_by = request.user)
        u=request.user
        channel.participants.add(u)
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
        all_user = channel.participants.all()
        if user not in all_user:
            channel.participants.add(user)
            channel.save()
        
        return redirect('channel', channel_id=channel_id)
    return HttpResponse('Some error Orrcured')