# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Permission(models.Model):
    "权限表"
    title = models.CharField(verbose_name="标题", max_length=32)
    url = models.CharField(verbose_name="含正则的URL", max_length=120)

    def __str__(self):
        return self.title

class Role(models.Model):
    "角色表"
    title = models.CharField(verbose_name="角色名称", max_length=32)
    permissions = models.ManyToManyField(verbose_name="拥有所有权限", to='Permission', blank=True)

    def __str__(self):
        return self.title

class UserInfo(AbstractUser):
    "用户表"
    # username = models.CharField(verbose_name='用户名', max_length=32)
    # password = models.CharField(verbose_name='密码', max_length=64)
    # email = models.CharField(verbose_name='邮箱', max_length=32)
    roles = models.ManyToManyField(verbose_name='拥有的所有角色', to='Role', blank=True)
    #
    # def __str__(self):
    #     return self.name
