from django import forms
from .models import Factory


class FactoryForm(forms.ModelForm):
    class Meta:
        model = Factory
        fields = ['code', 'name', 'country', 'contact']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
        }