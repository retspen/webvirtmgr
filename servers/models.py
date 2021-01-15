from django.db import models


class Compute(models.Model):
    name = models.CharField(max_length=20)
    hostname = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=14, blank=True, null=True)
    type = models.IntegerField()
    arch = models.CharField(max_length=20, default="x86_64")

    def __unicode__(self):
        return self.hostname
