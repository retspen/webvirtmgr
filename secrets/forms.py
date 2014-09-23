from django import forms


class AddSecret(forms.Form):
    ephemeral = forms.ChoiceField(required=True, choices=(('no', 'no'), ('yes', 'yes')))
    private = forms.ChoiceField(required=True, choices=(('no', 'no'), ('yes', 'yes')))
    usage_type = forms.ChoiceField(required=True, choices=(('ceph', 'ceph'), ('volume', 'volume'), ('iscsi', 'iscsi')))
    data = forms.CharField(max_length=100, required=True)
