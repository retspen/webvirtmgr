from django.db import models
from django.contrib.auth.models import User
from servers.models import Compute


class Instance(models.Model):
    compute = models.ForeignKey(Compute)
    name = models.CharField(max_length=20)
    uuid = models.CharField(max_length=36)
    acl = models.ManyToManyField(User, related_name='instance')
#    display_name = models.CharField(max_length=50)
#    display_description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
