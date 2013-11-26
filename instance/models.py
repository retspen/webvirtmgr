from django.db import models


class Host(models.Model):
    name = models.CharField(max_length=20)
    hostname = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=14, blank=True, null=True)
    type = models.CharField(max_length=3)

    def __unicode__(self):
        return self.hostname


class Flavor(models.Model):
    name = models.CharField(max_length=12)
    vcpu = models.IntegerField()
    ram = models.IntegerField()
    hdd = models.IntegerField()

    def __unicode__(self):
        return self.name


class Instance(models.Model):
    host = models.ForeignKey(Host)
    name = models.CharField(max_length=12)
    uuid = models.CharField(max_length=12)

    def __unicode__(self):
        return self.name
