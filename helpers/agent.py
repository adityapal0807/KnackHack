from .response import Responce
import json

from .prompts import generic_prompt
from .create_vector_db import CreateCollection
from .extract_from_pdf import convert_files_in_folder
import pandas as pd

import logging

logging.basicConfig(level=logging.INFO)

class Agent:
    def __init__(self, collection_name, data_directory, output_name):
        self.collection_name = collection_name
        self.data_directory = data_directory
        self.output_name = output_name
        self.collection_manager = CreateCollection()
        # self.data_creator = DataCreation(data_directory)
        self.memory = []

    def extract_data(self):
        convert_files_in_folder(self.data_directory, self.output_name)

    def check_exsisting_collection(self):
        try:
            self.db_collection = self.collection_manager.get_collection(self.collection_name)
            return True
        except: return False

    def create_db_collection(self):
        try:
            self.db_collection = self.collection_manager.get_collection(self.collection_name)
        except:
            data_df = pd.read_csv(f"{self.output_name}.csv")
            self.db_collection = self.collection_manager.db_collection(self.collection_name, fill_collection=True, data_df=data_df)
        print(self.db_collection)
        return self.db_collection

    def run_query(self, query):
        results = self.collection_manager.run_query(self.db_collection, query)
        return results

    def get_results(self, query):
        results = self.run_query(query)
        documents = results['documents']
        doc_dict = {}
        for i, doc in enumerate(documents[0]):
            doc_dict[f"Result {i}"] = doc

        doc_string = ""
        for key, value in doc_dict.items():
            doc_string += f"{key}: {value} \n \n "

        logging.info("Documents retreived...")
        print(doc_string)
        return doc_string

    def return_chunks(self, query):
        results = self.run_query(query)
        documents = results['documents']
        doc_dict = {}
        chunks = []
        for i, doc in enumerate(documents[0]):
            # doc_dict[f"Result {i}"] = doc
            chunks.append(doc)

        print(chunks)

        # doc_string = ""
        # for key, value in doc_dict.items():
        #     doc_string += f"{key}: {value} \n \n "

        # logging.info("Documents retreived...")
        # print(doc_string)
        # return doc_string
        return chunks

    def memory_manager(self, memory_content, role):
        self.memory.append({"role": f"{role}", "content": f"{memory_content}"})
        # If the memory has more than 5 messages (excluding the first system message), remove the oldest assistant message
        if len(self.memory) > 6:
            self.memory.pop(2)  # The oldest assistant message is at index 2


    def gpt_answer(self, query):
        responce = Responce()
        result_str = self.get_results(query)
        system_message = generic_prompt
        # Check if memory is empty
        if len(self.memory) == 0:
            # Add system message as the first message in memory
            self.memory_manager(system_message, "system")
        else:
            # Check if the first message in memory is not a system message
            if self.memory[0]["role"] != "system":
                # Add system message as the first message in memory
                self.memory.insert(0, {"role": "system", "content": system_message})

        query = f"""
        user_query = {query} \n
        result = {result_str} (retrived responces)\n
        """
        #  Add user query to memory
        self.memory_manager(query, "user")

        gpt_responce = responce.func_responce_mem(self.memory)
        # Add assistant responce to memory
        self.memory_manager(gpt_responce, "assistant")
        return gpt_responce

def main(collection_name, folder_path, output_name):
    # folder_path = r"C:\Users\abhin\OneDrive\Desktop\knack to hack code\files for rules"
    agent = Agent(collection_name, folder_path, output_name)
    query= '''AI Ethics,Responsible AI,Compliance Standards,Data Privacy,Ethical Guidelines,Risk Management,Legal Compliance,Regulatory Framework,AI Governance,Accountability,Transparency,Consent Management,Data Protection,Fairness,Bias Mitigation,Algorithmic Transparency,Security Measures,User Rights,Auditing Requirements,Impact Assessment'''
    if(agent.check_exsisting_collection()==True):
        answer=agent.gpt_answer(query)
        # print(answer)
        return answer
    else:
        agent.extract_data()
        agent.create_db_collection()
        answer=agent.gpt_answer(query)
        # print(answer)
        return answer


def create_new_collection(collection_name, folder_path, output_name="output"):
    agent= Agent(collection_name, folder_path, output_name)
    agent.extract_data()
    agent.create_db_collection()

def return_chunks_from_collection(query,collection_name, folder_path, output_name):
    agent= Agent(collection_name, folder_path, output_name)
    agent.create_db_collection()
    results= agent.return_chunks(query)
    return results

    
        

# main()
