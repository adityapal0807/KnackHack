from django.contrib.auth.models import AbstractUser
from django.db import models

class BaseModel(models.Model):
    uploaded_date = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    # Your custom fields here
    pass

class Rule(BaseModel):
    rule_number=models.CharField(max_length=50)
    rule_description=models.TextField()
    rule_threshold=models.IntegerField(default=10, choices=[(i, i) for i in range(1, 11)])

class FileCategory(BaseModel):
    file_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100) 


