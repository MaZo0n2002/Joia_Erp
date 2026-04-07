from django.db import models
from factories.models import Factory

# Create your models here.
class DPL(models.Model):
    title = models.CharField(max_length=100)
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    season = models.CharField(max_length=100)
    uploaded_file = models.FileField(upload_to='dpl_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title