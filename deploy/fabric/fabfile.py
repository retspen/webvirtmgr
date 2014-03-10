"""
Fabric Deployment script for WebvirtMgr
"""

from fabric.api import task
from fabtools.system import distrib_id

from utils import install_system_packages
from utils import get_webvirt
from utils import configure_nginx
from utils import configure_novnc
from utils import configure_supervisor


@task
def deploy_webvirt():
    """
    Install Webvirt on a Remote server
    """
    distro = distrib_id()
    install_system_packages(distro)
    get_webvirt()
    configure_nginx(distro)
    configure_novnc(distro)
    configure_supervisor(distro)


@task
def update_webvirt():
    """
    Update Webvirt on a Remote server
    Webvirt should be already installed
    """
    distro = distrib_id()
    get_webvirt()
    configure_nginx(distro)
    configure_supervisor(distro)
