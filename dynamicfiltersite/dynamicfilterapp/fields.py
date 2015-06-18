from django.db import models
from django.core.validators import RegexValidator
from django.core import validators

class CustomCommaSeparatedIntegerField(models.CharField):
    """
    custom-made comma separated integer field that specified input to be only 3 integers separated by commas
    """

    # contains additional custom RegexValidator
    default_validators = [validators.validate_comma_separated_integer_list, RegexValidator(r'^[0-9]+,[0-9]+,[0-9]+$')]

    def formfield(self, **kwargs):
        # contains custom error message
        defaults = {
            'error_messages': {
                'invalid': ('Enter only 3 integers separated by commas.'),
            }
        }
        defaults.update(kwargs)
        return super(CustomCommaSeparatedIntegerField, self).formfield(**defaults)