from django.contrib.auth.models import AbstractUser
from django.db import models

class BaseModel(models.Model):
    uploaded_date = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    # Your custom fields here
    pass

class Rule(BaseModel):
    rules_json = models.JSONField()

class FileCategory(BaseModel):
    file_name = models.CharField()
    category = models.CharField()    

