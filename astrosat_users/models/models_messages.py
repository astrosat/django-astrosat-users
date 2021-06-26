from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

###########
# helpers #
###########


def message_attachment_path(instance, filename):
    message = instance.message
    user = message.user
    return f"users/{user.username}/messages/{message.id}/attachments/{filename}"


########################
# managers & querysets #
########################


class MessageManager(models.Manager):
    pass


class MessageQuerySet(models.QuerySet):
    def read(self):
        return self.filter(read=True)

    def unread(self):
        return self.filter(read=False)

    def archived(self):
        return self.filter(archived=True)

    def unarchived(self):
        return self.filter(unarchived=False)


##########
# models #
##########


class Message(models.Model):
    """
    Stores a record of a message (ie: email) in the db
    """
    class Meta:
        ordering = ["-date"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    objects = MessageManager.from_queryset(MessageQuerySet)()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=512, blank=False, null=False)
    sender = models.CharField(max_length=512, blank=False, null=False)
    content = models.TextField()


class MessageAttachment(models.Model):
    """
    A simple little class for storing message attachments.
    Using a separate class to allow for multiple attachments per message.
    """
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )

    file = models.FileField(upload_to=message_attachment_path)

    def delete(self, *args, **kwargs):
        """
        When an attachment is deleted, delete the corresponding attatchment storage.
        """
        attachment_name = self.file.name
        attachment_storage = self.file.storage
        if attachment_storage.exists(attachment_name):
            attachment_storage.delete(attachment_name)

        return super().delete(*args, **kwargs)
