from django.db import models

# Create your models here.

class Factory(models.Model):
    code = models.CharField(max_length=50, blank=False)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=50)
    contact = models.CharField(max_length=100)
     
    def __str__(self):
        return self.name