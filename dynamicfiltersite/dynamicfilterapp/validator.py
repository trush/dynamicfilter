from django.core.exceptions import ValidationError

def validate_positive(value):
    """
    Validates that a number is positive. Used by the WorkerID model.
    """
    if value < 0:
        raise ValidationError('%s is not a positive number' % value)