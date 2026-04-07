from django import forms
from .models import DPL
from factories.models import Factory

STATUS_CHOICES = [
    ("incoming", "Incoming"),
    ("actual", "Actual"),
]

class DPLForm(forms.ModelForm):

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
        })
    )

    class Meta:
        model = DPL
        fields = ['title', 'factory', 'season', 'uploaded_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ FIX: dropdown
        self.fields['factory'].queryset = Factory.objects.all()

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 bg-white'
            })