from django.contrib import admin
from forms import RestaurantAdminForm

# Register models so they're accessible from admin site
from .models import Restaurant, RestaurantPredicate, Task

# RestaurantPredicates should be edited from the Restaurant page
# class RestaurantPredicateInline(admin.StackedInline):
#     model = RestaurantPredicate
#     # have space for 3 RestaurantPredicates by default
#     extra = 3
#     #readonly_fields = ('value',)


class RestaurantAdmin(admin.ModelAdmin):
    form = RestaurantAdminForm
    # fieldsets = [
    #     ('General Information', {'fields': ['name', 'url', 'text']}),
    #     ('Address', {'fields': ['street' ,'city', 'state', 'zipCode', 'country']})
    # ]
    # list_display = ('name',)
    # inlines = [RestaurantPredicateInline]

class TaskAdmin(admin.ModelAdmin):
    list_display = ('restaurantPredicate', 'workerID', 'answer', 'completionTime')

class RestaurantPredicateAdmin(admin.ModelAdmin):
    list_display = ('question', 'restaurant')

admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(RestaurantPredicate, RestaurantPredicateAdmin)