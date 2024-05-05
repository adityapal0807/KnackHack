import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

def make_openai_call_api(messages,model_name='gpt-3.5-turbo',temperature=0.7,stream:bool=False):
    request_payload = {
                'model': model_name,
                'temperature': temperature,
                'messages': messages,
                'stream': stream,
            }
    response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.getenv(f"OPENAI_KEY")}',
                'Content-Type': 'application/json',
            },
            json=request_payload,
            stream=stream,
        )
    print(response.text)
    res=json.loads(response.content.decode('utf-8'))
    res = res['choices'][0].get('message').get('content')
    print(res)
    return res
    # if stream == False:
    #     res=json.loads(response.content.decode('utf-8'))
    #     res = res['choices'][0].get('message').get('content')
    #     print(res)
    #     return res
    # else:
    #     for chunk in response.iter_lines():
    #         if chunk:
    #             payloads = chunk.decode().split("\n\n")
    #             for payload in payloads:
    #                 if '[DONE]' in payload:
    #                     break
    #                 if payload.startswith("data:"):
    #                     data = json.loads(payload.replace("data:", ""))
    #                     yield f"data: {json.dumps(data)}\n\n"



def make_openai_call_api_stream(messages,model_name='gpt-3.5-turbo',temperature=0.7):
    request_payload = {
                'model': model_name,
                'temperature': temperature,
                'messages': messages,
                'stream': True,
            }
    response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.getenv(f"OPENAI_KEY")}',
                'Content-Type': 'application/json',
            },
            json=request_payload,
            stream=True,
        )
    
    for chunk in response.iter_lines():
        if chunk:
            payloads = chunk.decode().split("\n\n")
            for payload in payloads:
                if '[DONE]' in payload:
                    break
                if payload.startswith("data:"):
                    data = json.loads(payload.replace("data:", ""))
                    yield f"data: {json.dumps(data)}\n\n"