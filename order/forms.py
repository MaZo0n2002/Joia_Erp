from django import forms
from .models import Quotation

class QuotationForm(forms.ModelForm):

    class Meta:
        model = Quotation
        fields = ["customer", "vat_percentage"]