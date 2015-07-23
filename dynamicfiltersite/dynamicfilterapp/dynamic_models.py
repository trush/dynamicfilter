from django.db import models
from django.core.cache import cache

def get_survey_response_model(restaurant):
    name = filter(str.isalpha, restaurant.name.encode('ascii', 'ignore'))
    # Collect the dynamic model's class attributes
    attrs = {
        '__module__': 'dynamicfilterapp.models', 
        '__unicode__': name
    }

    class Meta:
        app_label = 'responses'
        verbose_name = restaurant.name
    attrs['Meta'] = Meta

    # Add a field for each question
    for i in range(10):
        attrs['predicate' + str(i) + 'Status'] = models.IntegerField(default=5)
    # print attrs
    Restaurant = type('Restaurant', (models.Model,), attrs)
    
    return Restaurant