from django.db import models
from django.contrib.auth.models import User

class Host(models.Model):
    hostname = models.CharField(max_length=20)
    ipaddr = models.CharField(max_length=64)
    login = models.CharField(max_length=20)
    passwd = models.CharField(max_length=20)
    state = models.IntegerField()
    #snd_mail = models.IntegerField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.hostname
        
class Log(models.Model):
    host = models.ForeignKey(Host)
    type = models.CharField(max_length=20)
    message = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.message