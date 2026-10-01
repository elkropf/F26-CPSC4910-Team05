from django.db import models

# Create your models here.

# About page necessities
class About(models.Model):
    # Team and sprint information
    team_number =  models.CharField(max_length=3)
    sprint_number = models.CharField(max_length=2)
    release_date = models.DateField()
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()

    def __str__(self):
        return self.title