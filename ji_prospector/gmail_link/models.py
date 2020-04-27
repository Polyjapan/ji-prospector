from django.db import models

class MailboxConfig(models.Model):
    mailbox_email_adress = models.CharField(max_length=64, unique=True)
    prospector_client_id = models.CharField(max_length=64) # Given by Gmail API
    access_token = models.CharField(max_length=256) # Given by Gmail API
    refresh_token = models.CharField(max_length=256) # Given by Gmail API


class EmailAddress(models.Model):
    address = models.CharField(max_length=64, unique=True)
    ignore_unlinked = models.BooleanField(default=False)

    @property
    def see_in_gmail_url(self):
        pass

# Create your models here.
