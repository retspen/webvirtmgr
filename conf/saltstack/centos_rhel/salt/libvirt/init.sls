qemu-kvm:
  pkg.installed

libvirt:
  pkg.installed

/etc/libvirt/libvirtd.conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - source: salt://libvirt/libvirtd.conf
    - require:
      - pkg: libvirt

/etc/libvirt/qemu.conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - source: salt://libvirt/qemu.conf
    - require:
      - pkg: qemu-kvm

/etc/sysconfig/iptables:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - source: salt://libvirt/iptables

iptables:
  service:
    - dead
    - running

libvirtd:
  service:
    - running
    - enable: True

ksm:
  service:
    - running
    - enable: True

ksmtuned:
  service:
    - running
    - enable: True