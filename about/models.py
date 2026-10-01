from django.db import models

# Create your models here.

# Product info that doesn't change often.
class AboutProductInfo(models.Model):
    # Team and sprint information
    team_number =  models.CharField(max_length=3)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()

    def __str__(self):
        return self.title

class AboutSprintInfo(models.Model):
    sprint_number = models.CharField(max_length=2)
    release_date = models.DateField()
