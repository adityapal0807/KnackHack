import os
import asyncio
from openai import OpenAI
import json
import logging
from typing import Optional
import requests

from .open_ai_key import OPENAI_KYE
# from custom_functions import candidate_cv_info_extraction

# openai.api_key = OPENAI_KYE
client = OpenAI(api_key = OPENAI_KYE)



class Responce():
    def __init__(self,model: str = None) -> None:
        if model:
            self.model = model
        else:
            self.model = "gpt-3.5-turbo-1106"


    def func_responce(self, system_message, messages, func: Optional[object] = None, function: Optional[bool] = None):
        if function:
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"},
                functions=func,
                function_call='auto',
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": messages}
                ]
            )
            return json.loads(response.choices[0].message.function_call.arguments)
        else:
            print("WE ARE HERE")
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": messages}
                ]
            )
            return response.choices[0].message.content
        
    def func_responce_mem(self,message_list):
        logging.info("MESSAGE MEMORY %s", message_list)
        response = client.chat.completions.create(
            model=self.model,
            temperature=0.7,
            messages=message_list
        )
        text = response.choices[0].message.content
        text = text.replace('```json\n', '').replace('\n```', '')
        data = json.loads(text)
        return data
        
    def token_used(self,responce):
        print(responce)
        return responce['usage']['total_tokens']


def add_message(role, message , messages):
    messages.append({"role": role, "content": message})


def make_openai_call(messages,model_name='gpt-3.5-turbo',temperature=0.7):    
    request_payload = {
                'model': model_name,
                'temperature': temperature,
                'messages': messages,
            }
    response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': 'Bearer {OPENAI_KYE}',
                'Content-Type': 'application/json',
            },
            json=request_payload,
        )
    print(response)
    res = response.json()  # Parse response as JSON
    res = res['choices'][0].get('message').get('content')
    return json.loads(res)