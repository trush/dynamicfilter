from django.contrib import admin

# Register models so they're accessible from admin site
from .models import Restaurant, RestaurantPredicate, Task

# RestaurantPredicates should be edited from the Restaurant page
class RestaurantPredicateInline(admin.StackedInline):
    model = RestaurantPredicate
    # have space for 3 RestaurantPredicates by default
    extra = 3

class RestaurantAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Restaurant Information', {'fields': ['name', 'url', 'text']}),
    ]
    inlines = [RestaurantPredicateInline]

admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Task)