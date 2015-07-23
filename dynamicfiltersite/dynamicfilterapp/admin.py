from django.contrib import admin
from forms import RestaurantAdminForm

from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch

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
    readonly_fields = ('restaurant', 'value')

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False   

# Register models so they're accessible from admin site
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(RestaurantPredicate, RestaurantPredicateAdmin)
admin.site.register(PredicateBranch)