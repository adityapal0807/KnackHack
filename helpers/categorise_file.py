import openai
from wordcloud import WordCloud, STOPWORDS
import requests
import json
import re

# from text import text_content
from .open_ai_key import OPENAI_KYE
api_key=OPENAI_KYE

# where clause 
# function calling 
# query classificatioin
# query answer api

class FileTagger:
    def __init__(self, api_key):
        self.api_key = api_key
        self.stopwords = STOPWORDS
    
    def generate_wordcloud(self, text):
        wordcloud = WordCloud(stopwords=self.stopwords, background_color='white').generate(text)
        word_frequencies = wordcloud.words_
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        num_common_words = 50
        most_common_words = [word for word, count in sorted_words[:num_common_words]]
        return most_common_words
    
    def classify_text(self, text, categories):
        most_common_words = self.generate_wordcloud(text)
        messages = [
            {
                "role": "system",
                "content": "You are a very good text classifier. You re-evaluate your classifications to get the most confident results"
            },
            {
                "role": "user",
                "content": f"For the given most common words from a large file, try to understand the category of files these keywords are mostly used in and classify the file into one of the following categories.\nCATEGORIES: {categories}\nMOST COMMON WORDS: {most_common_words}\n Return the category and make sure to prefix the requested category with '```' exactly and suffix it with '```' exactly to get the answer."
            }
        ]
     
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': "gpt-3.5-turbo",
                'temperature': 0,
                'messages': messages
            }
        )

        resp = json.loads(response.content)
        resp = resp["choices"][0]["message"]["content"]
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, resp)
        if matches:
            category = matches[0].lower().strip()
            valid_categories = [item.lower().strip() for item in categories]
            if category in valid_categories:
                return category.capitalize(), most_common_words
            else:
                return "Miscellaneous", most_common_words
        else:
            return "Miscellaneous", most_common_words

class QueryTagger:
    def __init__(self, api_key):
        self.api_key= api_key

    def classify_query(self, text, categories, top_results):
        messages=[
            {
                "role":"system",
                "content": "You are a very good query classifier."
            },
            {
                "role":"user",
                "content":f"TOP RESULTS:{top_results}\n For the given query, accurately classify the query into one of the following categories using the top results which have most data/context related to that query. \n CATEGORIES:{categories}\n QUERY:{text} \n. Look for same/similar/matching keywords in the query and the top results and return the matching category.\n Use only the knowledge from top results for classification. Return the category and make sure to prefix the requested category with '```' exactly and suffix it with '```' exactly to get the answer."
            }
        ]

        response= requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model':'gpt-3.5-turbo',
                'temperature':0,
                'messages':messages
            }
        )

        resp= json.loads(response.content)
        resp= resp["choices"][0]["message"]["content"]
        # print(resp)
        pattern= r"```(.*?)```"
        matches= re.findall(pattern, resp)
        if matches:
            category= matches[0].lower().strip()
            valid_categories= [item.lower().strip() for item in categories]
            if category in valid_categories:
                return category.capitalize()
            else:
                return "Miscellaneous"
        else:
            return "Miscellaneous"

# if __name__ == "__main__":
#     file_tagger = FileTagger(api_key=api_key)
#     categories=['educational', 'financial', 'human resource', 'literary', 'personal']
    
#     category = file_tagger.classify_text(text=text_content, categories=categories)
#     print(category)