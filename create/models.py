from django.db import models


class Flavor(models.Model):
    label = models.CharField(max_length=50)
    memory = models.IntegerField()
    vcpu = models.IntegerField()
    disk = models.IntegerField()

    def __unicode__(self):
        return self.name
