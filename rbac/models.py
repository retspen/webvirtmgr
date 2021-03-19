# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class Button(models.Model):
    buttonname = models.CharField(verbose_name='按钮名称', max_length=64)
    pagename = models.CharField(verbose_name="反向url名称", max_length=64)

    def __str__(self):
        return self.buttonname + "." + self.pagename


class Menu(models.Model):
    """
    菜单表
    """
    menuname = models.CharField(verbose_name='菜单名称', max_length=64)
    pagename = models.CharField(verbose_name="反向url名称", max_length=64)
    children = models.CharField(verbose_name='菜单json', max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('menuname', 'pagename',)

    def __str__(self):
        return self.menuname + "." + self.pagename


class Permission(models.Model):
    "权限表"
    title = models.CharField(verbose_name="标题", max_length=32)
    method = models.CharField(verbose_name="请求方法", max_length=32)
    url = models.CharField(verbose_name="含正则的URL", max_length=120)

    class Meta:
        unique_together = ('title', 'method',)

    def __str__(self):
        return self.title + "." + self.method


class Role(models.Model):
    "角色表"
    title = models.CharField(verbose_name="角色名称", max_length=32)
    permissions = models.ManyToManyField(verbose_name="拥有所有权限", to='Permission', blank=True)
    menu = models.ManyToManyField(verbose_name='菜单权限', to="Menu", blank=True, help_text='null表示不是菜单；多级菜单看children')
    button = models.ManyToManyField(verbose_name='按钮权限', to="Button", blank=True)

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
