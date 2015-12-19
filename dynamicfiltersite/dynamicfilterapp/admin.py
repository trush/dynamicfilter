"""
Specifications for viewing/editing permission for admin page.
"""

from django.contrib import admin
from forms import RestaurantAdminForm

from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch

"""
Settings for Restaurant admin page.
"""
class RestaurantAdmin(admin.ModelAdmin):
    # the Restaurant admin view is customized using a form, in forms.py
    form = RestaurantAdminForm

"""
Settings for Task admin page.
"""
class TaskAdmin(admin.ModelAdmin):
    list_display = ('restaurantPredicate', 'workerID', 'answer', 'completionTime')

    def has_add_permission(self, request):
        return False
        
    # def has_delete_permission(self, request, obj=None):
    #     return False   

"""
Settings for RestaurantPredicate admin page.
"""
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
