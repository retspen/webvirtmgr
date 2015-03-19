"""
Fabric deployment script Utils
"""

import os

import settings as fsettings  # Fabric Deployment settings

from fabric.api import cd, sudo
from fabric.context_managers import settings
from fabric.contrib.files import append, contains

from fabtools import require, files
from fabtools.rpm import is_installed
from fabtools.supervisor import reload_config
from fabtools.nginx import disable as disable_site
from fabtools.python import install_requirements

# Local repo path
LOCAL_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "..", ".."))


def install_system_packages(distro):
    """
    Install system packages based on the Linux distribution of the remote node
    """
    if distro in ["Debian", "Ubuntu"]:
        require.deb.uptodate_index(max_age={'day': 7})
        return require.deb.packages(fsettings.DEBIAN_PKGS)
    elif distro in ["CentOS", "RHEL"]:
        if not is_installed(fsettings.CENTOS_EPEL[0]):
            fsettings.CENTOS_PKGS.append(fsettings.CENTOS_EPEL[1])
        return require.rpm.packages(fsettings.CENTOS_PKGS)
    elif distro in ["Fedora"]:
        return require.rpm.packages(fsettings.FEDORA_PKGS)

    raise RuntimeError("ERROR: Unrecognized OS!")


def get_webvirt():
    """
    Clone WebVirtMgr and Add it to installation location
    """
    require.directory(fsettings.INSTALL_PATH, use_sudo=True)
    with cd(fsettings.INSTALL_PATH):
        require.git.working_copy(fsettings.REPO_URL, use_sudo=True)

    webvirt_path = os.path.join(fsettings.INSTALL_PATH, "webvirtmgr")
    with cd(webvirt_path):
        install_requirements("requirements.txt", use_sudo=True)
        sudo("python manage.py syncdb")  # --noinput and load fixtures?!
        sudo("python manage.py collectstatic --noinput")  # just say yes!


def configure_nginx(distro):
    """
    Add Nginx configuration
    """
    # Local webvirtmgr site template
    conf = os.path.join(LOCAL_BASE_DIR, "deploy", "fabric", "templates",
                        "nginx.conf")
    # Remote location
    conf_path = os.path.join("/etc/nginx/conf.d", "webvirtmgr.conf")
    context = {
        "server_name": fsettings.SERVER_NAME
    }

    # Upload template to server
    files.upload_template(conf, conf_path, context=context, use_sudo=True)

    # Nginx, make sure `default` website is not running.
    if distro in ["Debian", "Ubuntu"]:
        disable_site("default")
    elif distro in ["Fedora"]:
        # Fedora places the default server:80 in nginx.conf!
        # we will replace nginx.conf
        default = "/etc/nginx/nginx.conf"
        default_bak = default + ".bak"

        # Local default nginx.conf template
        conf = os.path.join(LOCAL_BASE_DIR, "deploy", "fabric",
                            "templates", "original.nginx.conf")

        if not files.is_file(default_bak):
            # only replace backup if required
            sudo("mv %s %s" % (default, default + ".bak"))

        # Upload new nginx.conf to server
        files.upload_template(conf, default, use_sudo=True)
    else:
        default = "/etc/nginx/conf.d/default.conf"
        if files.is_file(default):
            sudo("mv %s %s" % (default, default + ".bak"))

    # Ensure running ...
    # require.nginx.server()
    require.service.restart("nginx")


def configure_novnc(distro):
    """
    Configure Websocket proxy (noVNC)
    """
    if distro in ["Debian", "Ubuntu"]:
        with settings(warn_only=True):
            sudo("service novnc stop")
            sudo("rm /etc/init.d/novnc")
        sudo("update-rc.d -f novnc remove")
        sudo("cp /var/www/webvirtmgr/conf/initd/webvirtmgr-console-ubuntu\
             /etc/init.d/webvirtmgr-console")
        sudo("service webvirtmgr-console start")
        sudo("update-rc.d webvirtmgr-console defaults")
        sudo("chown -R www-data:www-data /var/www/webvirtmgr")
    elif distro in ["CentOS", "RHEL", "Fedora"]:
        sudo("cp /var/www/webvirtmgr/conf/initd/webvirtmgr-console-redhat\
             /etc/init.d/webvirtmgr-console")
        sudo("service webvirtmgr-console start")
        sudo("chkconfig webvirtmgr-console on")
        sudo("chown -R nginx:nginx /var/www/webvirtmgr")


def configure_supervisor(distro):
    """
    Configure supervisor for running our WebVirtMgr Django Gunicorn Server
    """
    if distro in ["Debian", "Ubuntu"]:
        user = "www-data"
        require.supervisor.process(
            "webvirtmgr",
            command=
            "/usr/bin/python /var/www/webvirtmgr/manage.py run_gunicorn -c\
             /var/www/webvirtmgr/conf/gunicorn.conf.py",
            directory="/var/www/webvirtmgr",
            user=user,
            stdout_logfile="/var/log/supervisor/webvirtmgr.log",
            autostart=True,
            autorestart=True,
            redirect_stderr=True
        )
    elif distro in ["CentOS", "RHEL", "Fedora"]:
        # first, ensure supervisord is running!
        with settings(warn_only=True):
            require.service.restart("supervisord")
        supervisord = "/etc/supervisord.conf"
        if not contains(supervisord, "[program:webvirtmgr]"):
            f = open("templates/webvirtmgr.ini")
            content = f.read()
            f.close()
            append(supervisord, content, use_sudo=True)
            reload_config()
