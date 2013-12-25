from django.db import models


class InstanceLog(models.Model):
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.message