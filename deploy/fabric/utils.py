"""
Fabric deployment script Utils
"""

import os

import settings as fsettings  # Fabric Deployment settings

from fabric.api import cd, sudo
from fabric.context_managers import settings

from fabtools import require, files

# Local repo path
LOCAL_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 "..", ".."))


def install_system_packages(distro):
    """
    Install system packages based on the Linux distribution of the remote node
    """
    if distro in ["Debian", "Ubuntu"]:
        return require.deb.packages(fsettings.DEBIAN_PKGS)
    elif distro in ["CentOS", "RHEL"]:
        return require.rpm.packages(fsettings.CENTOS_PKGS)
    elif distro in ["Fedora"]:
        return require.rpm.packages(fsettings.FEDORA_PKGS)

    raise RuntimeError("ERROR: Unrecognized OS!")


def get_webvirt():
    """
    Clone WebVirtMgr and Add it to installation location
    """
    require.directory(fsettings.INSTALL_PATH)
    with cd(fsettings.INSTALL_PATH):
        require.git.working_copy(fsettings.REPO_URL)

    webvirt_path = os.path.join(fsettings.INSTALL_PATH, "webvirtmgr")
    with cd(webvirt_path):
        require.python.requirements("requirements.txt")
        sudo("python manage.py syncdb")  # --noinput and load fixture?!


def configure_nginx():
    """
    Add Nginx configuration
    """
    # Local template
    conf = os.path.join(LOCAL_BASE_DIR, "deploy", "fabric", "templates",
                        "nginx.conf")
    # Remote location
    conf_path = os.path.join("/etc/nginx/conf.d", "webvirtmgr.conf")
    context = {
        "server_name": fsettings.SERVER_NAME
    }

    # Upload template to server
    files.upload_template(conf, conf_path, context=context)

    # Nginx, make sure `default` website is not running.
    require.nginx.disabled("default")

    # Ensure running ...
    # require.nginx.server()
    require.service.started("nginx")


def configure_novnc(distro):
    """
    Configure Websocket proxy (noVNC)
    """
    if distro in ["Debian", "Ubuntu"]:
        with settings(warn_only=True):
            sudo("service novnc stop")
            sudo("rm /etc/init.d/novnc")
        sudo("update-rc.d -f novnc remove")
        sudo("cp /var/www/webvirtmgr/conf/initd/webvirtmgr-novnc-ubuntu\
             /etc/init.d/webvirtmgr-novnc")
        sudo("service webvirtmgr-novnc start")
        sudo("update-rc.d webvirtmgr-novnc defaults")
        sudo("chown -R www-data:www-data /var/www/webvirtmgr")
    elif distro in ["CentOS", "RHEL", "Fedora"]:
        sudo("cp /var/www/webvirtmgr/conf/initd/webvirtmgr-novnc-redhat\
             /etc/init.d/webvirtmgr-novnc")
        sudo("service webvirtmgr-novnc start")
        sudo("chkconfig webvirtmgr-novnc on")
        sudo("chown -R nginx:nginx /var/www/webvirtmgr")


def configure_supervisor(distro):
    """
    Configure supervisor for running our WebVirtMgr Django Gunicorn Server
    """
    if distro in ["Debian", "Ubuntu"]:
        user = "www-data"
    elif distro in ["CentOS", "RHEL", "Fedora"]:
        user = "nginx"

    require.supervisor.process(
        "webvirtmgr",
        command="/usr/bin/python /var/www/webvirtmgr/manage.py run_gunicorn -c\
         /var/www/webvirtmgr/conf/gunicorn.conf.py",
        directory="/var/www/webvirtmgr",
        user=user,
        stdout_logfile="/var/log/supervisor/webvirtmgr.log",
        autostart=True,
        autorestart=True,
        redirect_stderr=True
    )
