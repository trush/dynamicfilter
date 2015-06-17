from django.db import models
from django.core.validators import RegexValidator
from django.core import validators

class CustomCommaSeparatedIntegerField(models.CharField):
    default_validators = [validators.validate_comma_separated_integer_list, RegexValidator(r'^[0-9]+,[0-9]+,[0-9]+$')]

    def formfield(self, **kwargs):
        defaults = {
            'error_messages': {
                'invalid': ('Enter only 3 integers separated by commas.'),
            }
        }
        defaults.update(kwargs)
        return super(CustomCommaSeparatedIntegerField, self).formfield(**defaults)