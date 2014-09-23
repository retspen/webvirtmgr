from django.db import models
from servers.models import Compute


class Instance(models.Model):
    compute = models.ForeignKey(Compute)
    name = models.CharField(max_length=20)
    uuid = models.CharField(max_length=36)
    # display_name = models.CharField(max_length=50)
    # display_description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
