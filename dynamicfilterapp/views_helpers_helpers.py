from .models import *

def anyItems():
    return Item.objects.filter(isDone = False).exists()