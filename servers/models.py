from django.db import models


class Compute(models.Model):
    name = models.CharField(max_length=20)
    hostname = models.CharField(max_length=20)
    hypervisor = models.CharField(max_length=5)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=14, blank=True, null=True)
    type = models.IntegerField()

    def __unicode__(self):
        return self.hostname
