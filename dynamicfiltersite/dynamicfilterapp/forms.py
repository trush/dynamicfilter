from django import forms
from models import Restaurant, RestaurantPredicate

class WorkerForm(forms.Form):
    answer = forms.NullBooleanField(label='Your answer')

class RestaurantAdminForm(forms.ModelForm):

	class Meta:
		model = Restaurant
		fields = ['name', 'url', 'text', 'street']

	def save(self, commit=True):
		instance = super(RestaurantAdminForm, self).save(commit=False)
		if commit:
			instance.save()
		RestaurantPredicate.objects.create(restaurant=instance, question="Do they serve Austin Shin?")
		RestaurantPredicate.objects.create(restaurant=instance, question="Would you recommend the Kate Reed?")
		RestaurantPredicate.objects.create(restaurant=instance, question="Are you Prof Beth?")
		return instance
