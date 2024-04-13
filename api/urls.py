
from django.urls import path,include
from .views import *

urlpatterns = [
    path('register',User_Register.as_view()),
    path('get_view',GET_VIEW.as_view()),
    path('rules',RULES.as_view()),
    path('classify_query',Classify_Query.as_view()),
    path('injection',Injection.as_view()),
    path('check_pii',PII.as_view()),
    path('admin_panel',Admin_Panel.as_view()),
    path('summary',Generate_Summary.as_view()),


    
    # path('get_rules', get_rules),
    # path('create_rules', create_rules),
    # path('create_rules_new',create_rules_new),
    path('get_all_collections',get_all_collections),
    path('new_file_upload',new_file_upload),
    path('return_top_chunks',return_top_chunks),
    # path('query_classification', query_classification),
    # path('injection_check_api',injection_check_api),
    # path('check_pii',chatbot_with_pii),
    # path('streamed',streamed_response),

    path('change_rule_threshold',change_rule_threshold),
    path('add_rule',add_rule),
    path('delete_rule',delete_rule),
]
