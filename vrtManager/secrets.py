import base64
from vrtManager.connection import wvmConnect


class wvmSecrets(wvmConnect):
    def create_secret(self, ephemeral, private, secret_type, data):
        xml = """<secret ephemeral='%s' private='%s'>
                    <usage type='%s'>""" % (ephemeral, private, secret_type)
        if secret_type == 'ceph':
            xml += """<name>%s</name>""" % (data)
        if secret_type == 'volume':
            xml += """<volume>%s</volume>""" % (data)
        if secret_type == 'iscsi':
            xml += """<target>%s</target>""" % (data)
        xml += """</usage>
                 </secret>"""
        self.wvm.secretDefineXML(xml)

    def get_secret_value(self, uuid):
        secrt = self.get_secret(uuid)
        value = secrt.value()
        return base64.b64encode(value)

    def set_secret_value(self, uuid, value):
        secrt = self.get_secret(uuid)
        value = base64.b64decode(value)
        secrt.setValue(value)

    def delete_secret(self, uuid):
        secrt = self.get_secret(uuid)
        secrt.undefine()
