from django.db import models
from servers.models import Host


class Instance(models.Model):
    host = models.ForeignKey(Host)
    name = models.CharField(max_length=12)
    uuid = models.CharField(max_length=12)

    def __unicode__(self):
        return self.name
