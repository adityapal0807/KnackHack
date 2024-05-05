import pandas as pd
from typing import Optional, Union, List, Tuple
import chromadb 
from chromadb.config import Settings
import os
import re
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)


class CreateCollection:
    """Class to create and manage a collection in a chromadb database."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the CreateCollection class.

        Args:
            collection_name (str): The name of the collection to be created or managed.
            db_path (Optional[str]): The path to the database. Defaults to './db' if None.
        """
        self.db_path = db_path if db_path else './db'
        self.EXISTING_DB = False
        self.client = self._create_client()

    def _create_client(self):
        """Create a chromadb client."""
        return chromadb.PersistentClient(path=self.db_path, settings=Settings(allow_reset=True))

    def all_collections(self):
        # self.client = self._create_client()
        return self.client.list_collections()
    
    def get_collection(self,collection_name: str):
        # self.client = self._create_client()
        logging.info(self.client.list_collections())
        collection = self.client.get_collection(name=collection_name)
        return collection

    def delete_collection(self, collection_name):
        # self.client= self._create_client()
        self.client.delete_collection(name=collection_name)
        logging.info(f"Collection {collection_name} deleted")
    
    def create_collection(self, collection_name: str,category):
        """Create a new collection in the database."""
        # self.client = self._create_client()
        # client.reset()
        try:
            collection = self.client.get_collection(name=collection_name)
            logging.info("Database exists.")
            self.EXISTING_DB = True
        except:
            # self.client.reset()
            logging.info('Creating database...')
            collection = self.client.create_collection(collection_name,
                                                  metadata={"hnsw:space": "cosine", "category":category})
            self.EXISTING_DB = False
            logging.info(collection_name)
            logging.info(collection.count())
        return collection

    def fill_collection_csv(self, collection_name:str,sentence_df: pd.DataFrame):
        """Fill the collection with data from a CSV file."""
        logging.info("Filling database with data from CSV file...")
        try:
            df = sentence_df
        except Exception as e:
            logging.info(e)
            raise Exception("CSV file not found.")

        logging.info("Checking for Nan values...")
        # # Check for NaN values in the DataFrame
        # if df.isnull().values.any():
        #     raise ValueError("DataFrame contains NaN values.")
        
        try:
            # sentences = df['Info'].apply(lambda x: re.split('\.\s', x)).tolist()
            sentences= df['Content'].tolist()

            # for metadata
            file_name_list= df['file_name'].tolist()
            page_number_list=df['Page Number'].tolist()
            tokens_list=df['tokens'].to_list()
            image_data_list= df['Image_Data'].to_list()
            category_list= df['Category'].to_list()
            keywords_list= df['Keywords'].to_list()
            category= category_list[0]

            metadatas = []
            for i in range(len(file_name_list)):
                metadata={'file_name':file_name_list[i], 'page_number': page_number_list[i], 
                            'tokens': tokens_list[i], 'image_data': image_data_list[i], 'category':category_list[i], 'keywords':keywords_list[i]}
                metadatas.append(metadata)

            logging.info("META DATA LOADED............")
        except Exception as e:
            logging.info(e)
            raise Exception("CSV file not formatted correctly.")
        logging.info('CSV file loaded successfully.')

        db_collection = self.create_collection(collection_name,category)
        count = db_collection.count()
        # documents = [sentence[0] for sentence in sentences]
        documents = [sentence for sentence in sentences if isinstance(sentence, str) and sentence]  # Check for empty lists
        
        if count > 0:
            ids = [str(index + count +1) for index, _ in enumerate(sentences)]
        else:
            ids = [str(index + count) for index, _ in enumerate(sentences)]

        print(metadata)
        # if not self.EXISTING_DB:
        db_collection.add(documents=documents,
                                metadatas=metadatas,
                                ids=ids)
        logging.info(db_collection.count())
        logging.info("Database filled successfully.")

        # remove csv
        csv_file_path="output.csv"
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            print(f"The file '{csv_file_path}' has been successfully deleted.")
        else:
            print(f"The file '{csv_file_path}' does not exist.")
        return db_collection
    
    # Which collection to select If fill _collection =True then we need csv path so we can fill the csv
    def db_collection(self,collection_name:str, fill_collection:bool, data_df: Optional[pd.DataFrame]):
        self.fill_collection = fill_collection
        if fill_collection:
            # db_collection = collection_manager.create_collection()
            logging.info("Filling database with data from CSV FILE...")
            db_collection = self.fill_collection_csv(collection_name,data_df)  # If we want to add csv data to database
        else:
            db_collection = self.create_collection(collection_name,category="temp")
        logging.info(db_collection.count())
        
        return db_collection

                
    def run_query(self,collection, query: str) -> List[Tuple]:
        """Run a query against the collection."""
        results = collection.query(query_texts=[query], n_results=10)

        return results