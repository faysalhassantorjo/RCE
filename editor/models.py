from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.jpg')
    
    def imageURL(self):
        url = ''
        try:
            url = self.profile_picture.url
        except:
            url =''
        return url
    
    def __str__(self):
        return self.user.username
    
    
class CodeFile(models.Model):
    file_name = models.CharField(max_length=100, null=True,blank=True)
    file = models.TextField(blank=True,null=True)
    channel = models.ForeignKey('Channel',on_delete=models.CASCADE,related_name='channels_file', blank=True, null=True)
    date = models.DateTimeField(default=now, blank=True)
   
    def __str__(self) -> str:
        return f'file - {self.id}'
    
class Channel(models.Model):
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField(User)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    codefile = models.ManyToManyField(CodeFile,related_name='channels_file')
    channel_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.jpg')
    
    def imageURL(self):
        url = ''
        try:
            url = self.channel_picture.url
        except:
            url =''
        return url

    def __str__(self):
        return f"GroupRoom: {self.name}"
    
    
    # class GroupMessage(models.Model):
    # room = models.ForeignKey(GroupRoom, on_delete=models.CASCADE, related_name='messages')
    # sender = models.ForeignKey(User, on_delete=models.CASCADE)
    # message = models.TextField()
    # created_at = models.DateTimeField(auto_now_add=True)
    # is_code = models.BooleanField(default=False)

    # def __str__(self):
    #     return f"Message by {self.sender} in room {self.room.name}"
