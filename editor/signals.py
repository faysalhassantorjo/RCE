import docker
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserContainer

client = docker.from_env()

@receiver(post_save, sender=User)
def create_user_container(sender, instance, created, **kwargs):
    if created:
        container = client.containers.run(
            "user-code-executor",  # Image name
            detach=True,
            name=f"user_{instance.id}_container",
            hostname=f"user_{instance.id}",
        )
        UserContainer.objects.create(user=instance, container_id=container.id)
