from django.db import models

class Host(models.Model):
    hostname = models.CharField(max_length=12)
    ipaddr = models.IPAddressField()
    login = models.CharField(max_length=12)
    passwd = models.CharField(max_length=20)

    def __unicode__(self):
        return self.hostname
