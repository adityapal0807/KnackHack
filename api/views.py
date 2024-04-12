from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.http import StreamingHttpResponse

from .serializer import UserSerializer
from .models import User,Rule

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated  

from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from django.core.serializers import serialize

# get list of all collections
from helpers.agent import main
from helpers.create_vector_db import CreateCollection
from helpers.agent import create_new_collection, return_chunks_from_collection
from helpers.response import make_openai_call, add_message
from helpers.prompts import query_classification_prompt
from helpers.injection_check import run_injection_check
from helpers.pii import AnonymizerService
from helpers.base_api import make_openai_call_api

from .models import Rule,Organisation,Admin_Users,Queries

import os
import tempfile


# ADMIN APIS
# get api for queris (get all)
# rule threshold change api 
# rule add delete modify api
# api for number of type of violations -- ask mayank
# alert api's, as in prompt inject hui h to admin ko alert chala jae
# query safe/unsafe - general alert, prompt inject - high alert


# USER
# multiple collection me se query - chunks api
# summary/suggestion api for user for better usage/ safety score of user
# discuss mayank (mimic stream ya ek call dubara (jeck))



class User_Register(APIView):
    def post(self,request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(username=serializer.data['username'])
            token_obj,_ = Token.objects.get_or_create(user = user)
            # response['token'] = token_obj
            return Response({'payload':serializer.data,'token':str(token_obj),'message':'User created successfully'})
        return Response(serializer.errors)
    
class GET_VIEW(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        return Response({'payload':'success','user':str(request.user.username)})
    
@api_view(['POST'])
def create_rules(request):
    # provide dir containing compliance files and generate rules
    dir_path= request.data['dir_path']
    collection_name= "rules"
    output_name= "output"
    ans= main(collection_name, dir_path, output_name)

    # Register Rules in Organisation's Framework


    # TODO:     RULES  TO BE SAVED IN MODEL
    rule = Rule()
    rule.rules_json = ans
    rule.save()

    return Response({'rules':ans})


class RULES(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
    # GET RULES FOR ADMIN REGISTERED TO THAT ORGANISATION
        admin_org = Organisation.objects.all().get(org_admin=request.user)
        
        rules = Rule.objects.all().filter(org_id=admin_org.pk)
        # serialized_rules = serialize('json', rules)
        
        # Return the serialized data
        return Response({'rules':list(rules.values())})
    
    def post(self,request):
        uploaded_files= request.FILES.values()
    
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        for file_obj in uploaded_files:
            file_name = file_obj.name
            print(file_name)
            file_path = os.path.join(temp_dir, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_obj.read())

        collection_name= "rules"
        output_name= "output"
        ans= main(collection_name, temp_dir, output_name)

        # rules = ans['rules']
        # print(ans)
        try:
            admin_org = Organisation.objects.get(org_admin=request.user)
        except:
            return Response({'error':'Invalid Admin Credentials'})

        # print("rules: ",rules)
        for rule_number, rule_description in ans.items():
            print('here')
            # Extract rule number from key (e.g., "rule_1" -> "1")
            rule= Rule()
            rule.org_id = admin_org
            rule.rule_number = rule_number
            rule.rule_description = rule_description
            rule.save()

        # TODO:     RULES  TO BE SAVED IN MODEL
        # rule = Rule()
        # rule.rules_json = ans
        # rule.save()

        return Response({'rules':ans})
    

# @api_view(['POST'])
# def create_rules_new(request):
#     uploaded_files= request.FILES.values()
    
#     # Create a temporary directory
#     temp_dir = tempfile.mkdtemp()

#     for file_obj in uploaded_files:
#         file_name = file_obj.name
#         print(file_name)
#         file_path = os.path.join(temp_dir, file_name)
#         with open(file_path, 'wb') as f:
#             f.write(file_obj.read())

#     collection_name= "rules"
#     output_name= "output"
#     ans= main(collection_name, temp_dir, output_name)

#     # rules = ans['rules']
#     # print(ans)

#     # print("rules: ",rules)
#     for rule_number, rule_description in ans.items():
#         print('here')
#         # Extract rule number from key (e.g., "rule_1" -> "1")
#         rule= Rule()
#         rule.rule_number= rule_number
#         rule.rule_description= rule_description
#         rule.save()

#     # TODO:     RULES  TO BE SAVED IN MODEL
#     # rule = Rule()
#     # rule.rules_json = ans
#     # rule.save()

#     return Response({'rules':ans})  
# @api_view(['GET'])
# def get_rules(request):
#     # TODO  GET RULES FROM MODEL
#     rules = Rule.objects.first()
#     return Response({'rules':rules.rules_json})

@api_view(['GET'])
def get_all_collections(request):
    collection_manager= CreateCollection()
    collections = collection_manager.all_collections()
    names = [collection.name for collection in collections]
    categories= [collection.metadata for collection in collections]
    return Response({"collections":names, "categories":categories})

@api_view(['POST'])
def new_file_upload(request):
    file= request.data['file']
    print(file)

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Save the uploaded file into the temporary directory
    file_path = os.path.join(temp_dir, file.name)
    with open(file_path, 'wb') as f:
        f.write(file.read())
    
    # Extract filename without extension
    file_name_without_extension = os.path.splitext(file.name)[0]
    
    print(f"File saved to: {file_path}")
    print(f"Filename without extension: {file_name_without_extension}")
    create_new_collection(file_name_without_extension, temp_dir, output_name='output')

    return Response({"message":f"Collection {file_name_without_extension} created"})

@api_view(['POST'])
def return_top_chunks(request):
    # returns top chunks from a collection

    collection_name= request.data['collection_name']
    query= request.data['query']

    ans= return_chunks_from_collection(query,collection_name, folder_path='temp', output_name="output")
    # print("TOP CHUNKS:")
    
    return Response({'chunks':ans})
    

class Classify_Query(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        query= request.data['query']
        messages=[]
        add_message('system',query_classification_prompt,messages)
        add_message('user',f"query: {query}",messages)
        ans= make_openai_call_api(messages)
        ans= json.loads(ans)

        # TODO save info in user conversations
        obj = Queries()
        obj.user_id = request.user
        obj.query = query
        obj.category = ans.get('class')
        obj.description = ans.get('reason')
        obj.save()

        return Response(ans)
    
# @api_view(['POST'])
# def query_classification(request):
#     query= request.data['query']
#     messages=[]
#     add_message('system',query_classification_prompt,messages)
#     add_message('user',f"query: {query}",messages)
#     ans= make_openai_call_api(messages)
#     ans= json.loads(ans)
#     # TODO save info in user conversations

#     return Response({'response':ans})

class Injection(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        query= request.data['query']
        ans= run_injection_check(query)

        #save info in user conversations
        obj = Queries()
        obj.user_id = request.user
        obj.query = query
        obj.category = ans
        obj.description = 'Detected Prompt Injection by user. Generating alert to Admin'
        obj.save()

        return Response({"result":ans})
    
# @api_view(['POST'])
# def injection_check_api(request):
#     query= request.data['query']
#     ans= run_injection_check(query)
#     return Response({"result":ans})
anonymizer= AnonymizerService()

class PII(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    

    def post(self,request):
        question= request.data['query']

        # Collect RAG Chunks based on questions
        collection_name= request.data['collection_name']
        ans= return_chunks_from_collection(question,collection_name, folder_path='temp', output_name="output")


        # #STEP 1 Anonymize data
        anonymizer.reset_mapping()
        anonymized_question= anonymizer.anonymize_text(question)
        anonymized_chunks = anonymizer.anonymize_text(str(ans))

        #Step 2 Make OpenAi call
        messages=[]
        add_message('system', 'You are a very good data researcher.You are tasked with answering any question being asked.',messages)
        add_message('user',f"Answer the query based on the context provided. Give a very detailed answer.CONTEXT ::: {str(anonymized_chunks)} QUERY ::: {anonymized_question}.Provide output in Proper Format and Points such as bullet or numbered or underlining the important words",messages)

        response = make_openai_call_api(messages)

        # Step 3 DeAnonymize
        deanonymize_text = anonymizer.deanonymize_text(str(response))

        return Response({"gpt_response":response,"deanonymize":deanonymize_text})

# @api_view(['POST'])
# def chatbot_with_pii(request):


#     #TODO
#     # First send query for question classification
#     # If success 
#     #   Second check for prompt injection
#         # if caught
#         #     generate KeyError
#         # else
#         #     based on question gather rag chunks , anonymize them with the question and send to gpt
#         #     then after response deanonymize_text
#     # else
#     #   generate alert
    
#     question= request.data['query']

#     # Collect RAG Chunks based on questions
#     collection_name= request.data['collection_name']
#     ans= return_chunks_from_collection(question,collection_name, folder_path='temp', output_name="output")

#     # #STEP 1 Anonymize data
#     anonymizer= AnonymizerService()
#     anonymized_question= anonymizer.anonymize_text(question)
#     anonymized_chunks = anonymizer.anonymize_text(str(ans))

#     #Step 2 Make OpenAi call
#     messages=[]
#     add_message('user',f"Answer the query based on the context provided.CONTEXT ::: {str(anonymized_chunks)} QUERY ::: {anonymized_question}",messages)
#     print(messages)
#     response = make_openai_call_api(messages)

#     # Step 3 DeAnonymize
#     deanonymize_text = anonymizer.deanonymize_text(str(response))

#     return Response({"gpt_response":response,"deanonymize":deanonymize_text})

def get_response(messages,stream:bool=True):
        if stream:
            for result in make_openai_call_api(messages=messages,stream=stream):
                yield result

def streamed_response(request):
    text = request.data['query']
    messages = []
    add_message('user',f"Return the text as at is without making any changes or additional text . TEXT : {text}")
    return StreamingHttpResponse(get_response(messages=messages), content_type='text/event-stream')