from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.jpg')
    last_activity = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    # theme = models.CharField(max_length=50, default="default")
    def imageURL(self):
        url = ''
        try:
            url = self.profile_picture.url
        except:
            url =''
        return url
    def is_user_online(self):
        now = timezone.now()
        if now - self.last_activity < timedelta(minutes=1):
            self.is_online = True
            self.save()
            return True
        return False
    def __str__(self):
        return self.user.username



class UserContainer(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    container_id = models.CharField(max_length=64)
    installed_packages = models.TextField(null=True,blank=True)
    
    def __str__(self):
        return f'{self.id}'
    
class CodeFile(models.Model):
    file_name = models.CharField(max_length=100, null=True,blank=True)
    file = models.TextField(blank=True,null=True)
    channel = models.ForeignKey('Channel',on_delete=models.CASCADE,related_name='channels_file', blank=True, null=True)
    date = models.DateTimeField(default=now, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='users_file')
   
    def __str__(self) -> str:
        return f'{self.file_name}'
    
class Channel(models.Model):
    LANGUAGES={
        'PYTHON':'python3.12.3',
        'C': 'gcc 13.3.0',
        'JAVA': 'openjdk 21.0.2',
    }
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField(UserProfile)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    codefile = models.ManyToManyField(CodeFile,related_name='channels_file')
    channel_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.jpg')
    programing_language = models.CharField(max_length=255,choices=LANGUAGES, default="PYTHON")
    has_permission = models.ManyToManyField(UserProfile, blank=True, related_name='task_permission')
    def imageURL(self):
        url = ''
        try:
            url = self.channel_picture.url
        except:
            url =''
        return url

    def __str__(self):
        return f"GroupRoom: {self.name}"
    
class DMRoom(models.Model):
    participant = models.ManyToManyField(UserProfile)
    
    def __str__(self):
        return f'Room id: {self.id}'
        
    
class RoomMessage(models.Model):
    room = models.ForeignKey(DMRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender} in room {self.room.name}"

class ReadStatus(models.Model):
    """Tracks if a message has been read by a user."""
    message = models.ForeignKey(RoomMessage, related_name='read_statuses', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, related_name='read_statuses', on_delete=models.CASCADE)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Read status for {self.user.username} on message {self.message.pk}"

class GlobalChatRoom(models.Model):
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    send_at = models.DateTimeField(auto_now_add=True)
    
class LabTest(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name="labtest")
    title = models.CharField(max_length=200, blank=True, null=True)
    text_question = models.TextField(null=True, blank=True)
    raw_question_text = models.TextField(null=True,blank=True)
    image_question = models.ImageField(upload_to='lab-question/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    available = models.BooleanField(default=False)
    duration = models.IntegerField(default=10)
    
    start_at = models.TimeField(auto_now_add=True, null=True, blank=True)
    end_at = models.TimeField(auto_now_add=False, null=True, blank=True)

    
    def imageURL(self):
        url = ''
        try:
            url = self.image_question.url
        except:
            url =''
        return url

class AttemptTest(models.Model):
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name="labtest_attempt")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_attempt_test")
    char_deltas = models.JSONField(null=True, blank=True)
    time_labels = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.TextField(null=True, blank=True)
    attempt_at = models.TimeField(null=True, blank=True)
    done = models.BooleanField(default=False)
    

class AttemptPaste(models.Model):
    attempt_test = models.ForeignKey(AttemptTest, on_delete=models.CASCADE,related_name='pasted_attempt_test')
    content = models.TextField(null=True,blank=True)
    start_line = models.PositiveIntegerField(default=0)
    end_line = models.PositiveIntegerField(default=0)
