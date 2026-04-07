from django import forms
from customers.models import Customer

class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ['code', 'name', 'email', 'phone_number', 'address']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
        }
  