from django.db import models
from django.utils import timezone

class User(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    email = models.EmailField(default="")

    def __str__(self):
        return self.username


class Insurance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insurances', null=True, default=1)
    insurance_id = models.CharField(max_length=50)
    expiry_date = models.DateTimeField()
    starting_date = models.DateTimeField()
    car_brand = models.CharField(max_length=50)
    car_model = models.CharField(max_length=50)
    VIN = models.CharField(max_length=50)

    class Meta:
        unique_together = ['user', 'insurance_id']

    def __str__(self):
        return f"{self.insurance_id} - {self.car_brand} {self.car_model}"

