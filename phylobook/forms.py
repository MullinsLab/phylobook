from django.contrib.auth.forms import PasswordResetForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML


class PasswordResetFormExtra(PasswordResetForm):
    def __init__(self, *args, **kw):
        super(PasswordResetFormExtra, self).__init__(*args, **kw)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            'email',
            Div(
               Submit('submit', 'Reset password', css_class='btn btn-default'),
               HTML('<a class="btn btn-default" href="/">Cancel</a>'),
               css_class='text-left',
            )
        )
