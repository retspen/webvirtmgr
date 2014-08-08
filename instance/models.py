from django.db import models
from django.contrib.auth.models import User
from servers.models import Compute


class Instance(models.Model):
    compute = models.ForeignKey(Compute)
    name = models.CharField(max_length=20)
    uuid = models.CharField(max_length=36)
<<<<<<< HEAD
    acl = models.ManyToManyField(User, related_name='instance')
#    display_name = models.CharField(max_length=50)
#    display_description = models.CharField(max_length=255)
=======
    # display_name = models.CharField(max_length=50)
    # display_description = models.CharField(max_length=255)
>>>>>>> 57daf9f72f6f1c81531deaa15c74d74f1d7a280d

    def __unicode__(self):
        return self.name
