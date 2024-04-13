from django.contrib.auth.models import AbstractUser
from django.db import models

class BaseModel(models.Model):
    uploaded_date = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    # Your custom fields here
    pass

class FileCategory(BaseModel):
    file_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100) 

class Admin_Users(BaseModel):
    admin_name = models.ForeignKey(User,on_delete=models.CASCADE,related_name='admin_name')
    sub_user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='sub_user')

class Organisation(BaseModel):
    org_admin = models.ForeignKey(User,on_delete=models.CASCADE,related_name='org_admin')
    org_name = models.CharField(max_length=100)

class Rule(BaseModel):
    org_id = models.ForeignKey(Organisation,on_delete=models.CASCADE,related_name='org_id')
    rule_number=models.CharField(max_length=50)
    rule_description=models.TextField()
    rule_threshold=models.IntegerField(default=10, choices=[(i, i) for i in range(1, 11)])

class Queries(BaseModel):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,related_name='admin_id')
    query = models.TextField()
    query_type = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField()

    

