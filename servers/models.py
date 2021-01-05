from django.db import models


class Compute(models.Model):
    ARCH_TYPE = (('arm','AARCH64'),('x86','X_86'))
    name = models.CharField(max_length=20)
    hostname = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=14, blank=True, null=True)
    arch = models.CharField(max_length=20, choices=ARCH_TYPE, default='x86')
    type = models.IntegerField()

    def __unicode__(self):
        return self.hostname
