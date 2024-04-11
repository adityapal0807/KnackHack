
from django.urls import path,include
from .views import *

urlpatterns = [
    path('register',User_Register.as_view()),
    path('get_view',GET_VIEW.as_view()),
    
    path('get_rules', get_rules),
    path('create_rules', create_rules),
    path('get_all_collections',get_all_collections),
    path('new_file_upload',new_file_upload),
    path('return_top_chunks',return_top_chunks),
    path('query_classification', query_classification),
    path('injection_check_api',injection_check_api),
    path('check_pii',chatbot_with_pii)
]
