from django.contrib import admin
from forms import RestaurantAdminForm

# Register models so they're accessible from admin site
from .models import Restaurant, RestaurantPredicate, Task

class RestaurantAdmin(admin.ModelAdmin):
    form = RestaurantAdminForm

class TaskAdmin(admin.ModelAdmin):
    list_display = ('restaurantPredicate', 'workerID', 'answer', 'completionTime')

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False   

class RestaurantPredicateAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'question')
    readonly_fields = ('restaurant', 'question', 'value', 'leftToAsk')

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False   

admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(RestaurantPredicate, RestaurantPredicateAdmin)