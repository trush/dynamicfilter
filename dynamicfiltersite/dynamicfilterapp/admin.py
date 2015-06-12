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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False   

class RestaurantPredicateAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'question')
    readonly_fields = ('restaurant', 'question', 'value', 'leftToAsk')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False   

admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(RestaurantPredicate, RestaurantPredicateAdmin)