"""
Settings for deploying WebVirtMgr on a remote node
Used by fabfile.py
"""

DEBIAN_PKGS = [
    "git", "python-pip", "python-libvirt", "python-libxml2", "novnc",
    "supervisor", "nginx"
]

FEDORA_PKGS = [
    "git", "python-pip", "libvirt-python", "libxml2-python", "supervisor",
    "nginx", "python-websockify"
]

CENTOS_PKGS = [
    "git", "python-pip", "libvirt-python", "libxml2-python", "supervisor",
    "nginx", "python-websockify"
]
# Extra Centos package
CENTOS_EPEL = (
    "epel-release-6-8.noarch",
    "http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm"
)

REPO_URL = "https://github.com/retspen/webvirtmgr.git"
INSTALL_PATH = "/var/www/"

# NGINX server name
SERVER_NAME = "webvirt.local"
