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
from helpers.prompts import query_classification_prompt,safety_prompt, pii_prompt, general_pii_prompt
from helpers.injection_check import run_injection_check
from helpers.pii import AnonymizerService
from helpers.base_api import make_openai_call_api,make_openai_call_api_stream

from .models import Rule,Organisation,Admin_Users,Queries

import os
import tempfile


# ADMIN APIS
# get api for queris (get all) --done
# rule threshold change api  --done
# rule add delete modify api --done
# api for number of type of violations -- ask mayank --done
# alert api's, as in prompt inject hui h to admin ko alert chala jae --Flagged Users
# query safe/unsafe - general alert, prompt inject - high alert 

# category of document


# USER
# multiple collection me se query - chunks api -- done
# summary/suggestion api for user for better usage/ safety score of user 
# discuss mayank (mimic stream ya ek call dubara (jeck))

#All users queries api




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
    

@api_view(['POST'])
def change_rule_threshold(request):
    rule_number= request.data['rule_number']
    try:
        rule = Rule.objects.get(rule_number=f"rule_{rule_number}")
    except Rule.DoesNotExist:
        return Response({"error": "Rule not found"}, status=404)

    new_threshold = request.data.get('new_threshold')
    if new_threshold is None:
        return Response({"error": "New threshold not provided"}, status=400)

    rule.rule_threshold = new_threshold
    rule.save()

    return Response({"message":f"Threshold for rule {rule_number} changed to {new_threshold}"})

@api_view(['POST'])
def add_rule(request):
    rule_number = request.data.get('rule_number')
    rule_description = request.data.get('rule_description')
    rule_threshold = request.data.get('rule_threshold')

    if not (rule_number and rule_description and rule_threshold):
        return Response({"error": "Incomplete rule data provided"}, status=400)

    admin_org = Organisation.objects.all().get(org_admin=request.user)


    rule = Rule.objects.create(
        org_id=admin_org,
        rule_number=f"rule_{rule_number}",
        rule_description=rule_description,
        rule_threshold=rule_threshold
    )

    return Response({
        "rule_number": rule.rule_number,
        "rule_description": rule.rule_description,
        "rule_threshold": rule.rule_threshold
    }, status=201)


@api_view(['POST'])
def delete_rule(request):
    rule_number= request.data['rule_number']
    print(rule_number)
    try:
        rule = Rule.objects.get(rule_number=f"rule_{rule_number}")
    except Rule.DoesNotExist:
        return Response({"error": "Rule not found"}, status=404)

    rule.delete()
    return Response({"message":'rule deleted'},status=200)

@api_view(['DELETE'])
def delete_all_rules(request):

    # delete from models
    try:
        Rule.objects.all().delete()
    except:
        pass

    # delete rules collection
    try:
        collection_manager= CreateCollection()
        collection_manager.delete_collection("rules")
    except:
        pass

    return Response({"message": "All rules have been deleted"}, status=200)


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

# @api_view(['POST'])
# def return_top_chunks(request):
#     # returns top chunks from a collection

#     collection_name= request.data['collection_name']
#     query= request.data['query']

#     ans= return_chunks_from_collection(query,collection_name, folder_path='temp', output_name="output")
#     # print("TOP CHUNKS:")
    
#     return Response({'chunks':ans})
    
@api_view(['POST'])
def return_top_chunks(request):
    collection_data = request.data.get('collections', None)
    query = request.data.get('query', None)

    # Check for required data
    if not collection_data or not query:
        return Response({'error': 'Missing required data (collections and query)'}, status=400)

    # Initialize an empty list to store all chunks
    all_chunks = []
    print('collection_data', collection_data)
    # Extract collection names from request data
    collection_names = []
    for key, value in collection_data.items():
        if key.startswith('collection_name_'):
            # Extract number from key
            try:
                number = int(key.split('_')[-1])
                collection_names.append(value)
            except ValueError:
                # Ignore invalid format
                pass

    # Check if any valid collections were extracted
    if not collection_names:
        return Response({'error': 'Invalid collection name format'}, status=400)

    # Loop through each collection and retrieve chunks
    for collection_name in collection_names:
        try:
            chunks = return_chunks_from_collection(query, collection_name, folder_path='temp', output_name="output")
            all_chunks.append(chunks)  # Add chunks to the combined list
        except Exception as e:
            # Handle errors gracefully (e.g., log the error)
            return Response({'error': f'Error processing collection {collection_name}'}, status=500)

    # Return response with all collected chunks
    return Response({'chunks': all_chunks})



class Classify_Query(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        query= request.data['query']
        rules = Rule.objects.all()

        # Concatenate rule numbers and descriptions into a single string
        rules_string = "\n".join([f"{rule.rule_number}: {rule.rule_description} \n {rule.rule_number}_Threshold: {rule.rule_threshold}" for rule in rules])
        print(rules_string)

        messages=[]
        add_message('system',query_classification_prompt(rules_string),messages)
        add_message('user',f"query: {query}",messages)
        ans= make_openai_call_api(messages)
        ans= json.loads(ans)

        # TODO save info in user conversations
        if str(ans.get('class')) == 'Unsafe':
            obj = Queries()
            obj.user_id = request.user
            obj.query = query
            obj.query_type = 'Query Classification'
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
        if ans=='Prompt Injection Detected':
            obj = Queries()
            obj.user_id = request.user
            obj.query = query
            obj.query_type = 'Prompt Injection'
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
        # question= request.data['query']

        # Collect RAG Chunks based on questions
        # collection_name= request.data['collection_name']
        # ans= return_chunks_from_collection(question,collection_name, folder_path='temp', output_name="output")
        
        query = request.data.get('query', None)
        collection_data = request.data.get('collections', None)
        if len(collection_data) != 0:
            
            # Check for required data
            if not collection_data or not query:
                return Response({'error': 'Missing required data (collections and query)'}, status=400)

            # Initialize an empty list to store all chunks
            all_chunks = []
            # print('collection_data', collection_data)
            # Extract collection names from request data
            collection_names = []
            for key, value in collection_data.items():
                if key.startswith('collection_name_'):
                    # Extract number from key
                    try:
                        number = int(key.split('_')[-1])
                        collection_names.append(value)
                    except ValueError:
                        # Ignore invalid format
                        pass

            # Check if any valid collections were extracted
            if not collection_names:
                return Response({'error': 'Invalid collection name format'}, status=400)

            # Loop through each collection and retrieve chunks
            for collection_name in collection_names:
                try:
                    chunks = return_chunks_from_collection(query, collection_name, folder_path='temp', output_name="output")
                    all_chunks.append(chunks)  # Add chunks to the combined list
                except Exception as e:
                    # Handle errors gracefully (e.g., log the error)
                    # return Response({'error': f'Error processing collection {collection_name}'}, status=500)
                    continue

            # #STEP 1 Anonymize data

            anonymized_question= anonymizer.anonymize_text(query)
            anonymized_chunks = anonymizer.anonymize_text(str(all_chunks))

            #Step 2 Make OpenAi call
            messages=[]
            add_message('system', pii_prompt,messages)
            add_message('user',f"Answer the query based on the context provided .CONTEXT ::: {str(anonymized_chunks)} QUERY ::: {anonymized_question}.Provide output in Proper Format and Points such as bullet or numbered or underlining the important words",messages)

            response = make_openai_call_api(messages)

            # Step 3 DeAnonymize
            deanonymize_text = anonymizer.deanonymize_text(str(response))
            print(anonymizer.anonymizer.deanonymizer_mapping)

            messages_stream = []
            add_message('user',f"Return the text as at is without making any changes or additional text . TEXT : {deanonymize_text}",messages_stream)

            #Save in Database
            obj = Queries()
            obj.user_id = request.user
            obj.query = query
            obj.query_type = 'Safe'
            obj.category = 'Safe'
            obj.description = "Query Safe , Following all organisation's compliance"
            obj.save()

            # return Response({"gpt_response":response,"deanonymize":deanonymize_text})
            # print(self.get_response(messages=messages))
            return StreamingHttpResponse(self.gpt_stream(messages=messages_stream), content_type='text/event-stream')
        else:
            messages=[]
            add_message('system', general_pii_prompt, messages)
            add_message('user',f"Answer the query QUERY ::: {query}.Provide output in Proper Format and Points such as bullet or numbered or underlining the important words",messages)
            obj = Queries()
            obj.user_id = request.user
            obj.query = query
            obj.query_type = 'Safe'
            obj.category = 'Safe'
            obj.description = "Query Safe , Following all organisation's compliance"
            obj.save()

            return StreamingHttpResponse(self.gpt_stream(messages=messages), content_type='text/event-stream')

    
    def gpt_stream(self,messages):
        for result in make_openai_call_api_stream(messages=messages):
            yield result

        anonymizer.reset_mapping()
            
class Admin_Panel(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        response = {}
        sub_users = Admin_Users.objects.all().filter(admin_name=request.user)
        for user in sub_users:
        # Initialize an empty list to store queries for the current user
            user_queries = []
            
            # Get all queries associated with the current user
            queries = Queries.objects.filter(user_id=user.sub_user)
            for query in queries:
                # Create a dictionary for each query
                query_data = {
                    'query': query.query,
                    'type':query.query_type,
                    'category': query.category,
                    'description': query.description,
                    'create_at':query.uploaded_date

                }
                
                # Append the query dictionary to the user_queries list
                user_queries.append(query_data)
            
            # Add the list of queries to the response dictionary with the username as the key
            response[user.sub_user.username] = user_queries

        return Response(response)
    
# class User_Panel
class Generate_Summary(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):

        username = request.data.get('username', None)
        queries = Queries.objects.all().filter(user_id=User.objects.get(username=username))
        chat_history=[]
        for query in queries:
                # Create a dictionary for each query
                query_data = {
                    'query': query.query,
                    'type':query.query_type,
                    'category': query.category,
                    'description': query.description,
                }
                
                # Append the query dictionary to the user_queries list
                chat_history.append(query_data)
        
        messages=[]
        add_message('system',safety_prompt,messages)
        add_message('user',f'CHAT HISTORY : {chat_history}',messages)

        #remove for stream
        # response = make_openai_call_api(messages)

        return StreamingHttpResponse(self.gpt_stream(messages=messages), content_type='text/event-stream')
        # return Response({"gpt_response":response})

    def gpt_stream(self,messages):
        for result in make_openai_call_api_stream(messages=messages):
            yield result



            






