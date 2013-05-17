from django.db import models


class Host(models.Model):
    hostname = models.CharField(max_length=20)
    ipaddr = models.IPAddressField()
    login = models.CharField(max_length=12)
    passwd = models.CharField(max_length=14, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    conn_type = models.CharField(max_length=3)
    ssh_port = models.IntegerField(default='22')

    def __unicode__(self):
        return self.hostname


class Flavor(models.Model):
    name = models.CharField(max_length=12)
    vcpu = models.IntegerField()
    ram = models.IntegerField()
    hdd = models.IntegerField()

    def __unicode__(self):
        return self.name


class Vm(models.Model):
    host = models.ForeignKey(Host)
    vname = models.CharField(max_length=12)
    vnc_passwd = models.CharField(max_length=12)

    def __unicode__(self):
        return self.vname
