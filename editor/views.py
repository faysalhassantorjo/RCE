from django.shortcuts import render,redirect
from .tasks import message
from .models import *
from django.http import HttpResponse
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
    print(channels)
    context={
        'channels':channels,
        'users':users
    }
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

