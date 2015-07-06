from django.core.exceptions import ValidationError

def validate_positive(value):
    if value < 0:
        raise ValidationError('%s is not a positive number' % value)