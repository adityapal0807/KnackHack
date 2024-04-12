from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.serializers import serialize

from .serializer import UserSerializer
from .models import User,Rule

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated  

from rest_framework.decorators import api_view
from rest_framework.response import Response
import json

# get list of all collections
from helpers.agent import main
from helpers.create_vector_db import CreateCollection
from helpers.agent import create_new_collection, return_chunks_from_collection
from helpers.response import make_openai_call, add_message
from helpers.prompts import query_classification_prompt
from helpers.injection_check import run_injection_check
from helpers.pii import AnonymizerService
from helpers.base_api import make_openai_call_api

from .models import Rule

import os
import tempfile

anonymizer= AnonymizerService()


# file me se rules --done
# rules ka model theek --done
# queries model
# chunk size-512 -- done
# multiple collection me se query
# auth-pal


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

    # TODO:     RULES  TO BE SAVED IN MODEL
    rule = Rule()
    rule.rules_json = ans
    rule.save()

    return Response({'rules':ans})

@api_view(['POST'])
def create_rules_new(request):
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

    # print("rules: ",rules)
    for rule_number, rule_description in ans.items():
        print('here')
        # Extract rule number from key (e.g., "rule_1" -> "1")
        rule= Rule()
        rule.rule_number= rule_number
        rule.rule_description= rule_description
        rule.save()

    # TODO:     RULES  TO BE SAVED IN MODEL
    # rule = Rule()
    # rule.rules_json = ans
    # rule.save()

    return Response({'rules':ans})


@api_view(['GET'])
def get_rules(request):
    # Serialize the queryset of Rule objects into JSON format
    rules = Rule.objects.all()
    serialized_rules = serialize('json', rules)

    # Return the serialized data
    return Response(serialized_rules)

@api_view(['GET'])
def get_all_collections(request):
    collection_manager= CreateCollection()
    collections = collection_manager.all_collections()
    names = [collection.name for collection in collections]
    return Response({"collections":names})

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
    
    return Response({'chunks':ans})
    

@api_view(['POST'])
def query_classification(request):
    query= request.data['query']
    messages=[]
    add_message('system',query_classification_prompt,messages)
    add_message('user',f"query: {query}",messages)
    ans= make_openai_call(messages)

    # TODO save info in user conversations

    return Response(ans)


@api_view(['POST'])
def injection_check_api(request):
    query= request.data['query']
    ans= run_injection_check(query)
    return Response({"result":ans})



@api_view(['POST'])
def chatbot_with_pii(request):

    #TODO
    # First send query for question classification
    # If success 
    #   Second check for prompt injection
        # if caught
        #     generate KeyError
        # else
        #     based on question gather rag chunks , anonymize them with the question and send to gpt
        #     then after response deanonymize_text
    # else
    #   generate alert
    
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
    add_message('user',f"Answer the query based on the context provided.CONTEXT ::: {str(anonymized_chunks)} QUERY ::: {anonymized_question}",messages)
    print(messages)
    response = make_openai_call_api(messages)

    # Step 3 DeAnonymize
    deanonymize_text = anonymizer.deanonymize_text(str(response))

    return Response({"gpt_response":response,"deanonymize":deanonymize_text})