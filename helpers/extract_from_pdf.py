import fitz
import os
from ftfy import fix_text
import csv
import pandas as pd
import re

from PIL import Image
import base64

from .categorise_file import FileTagger
from .semantic_chunk_splitter import SentenceSplitter
from .open_ai_key import OPENAI_KYE
api_key=OPENAI_KYE



class PDFToCSVConverter:
    def __init__(self, pdf_path, csv_file_name, mode='page'):
        self.pdf_path = pdf_path
        self.csv_file_name = csv_file_name
        self.mode = mode.lower()
        self.pdf_document = None
        self.total_text=''

    def open_pdf(self):
        self.pdf_document = fitz.open(self.pdf_path)

    def close_pdf(self):
        if self.pdf_document:
            self.pdf_document.close()

    def extract_text_from_page(self, page_number):
        page = self.pdf_document.load_page(page_number)
        text = page.get_text()
        # text= self.fix_text(text)
        return text


    def extract_text_from_all_pages(self, mode="page"):
        extracted_data = {}
        data_str=''
        print('mode:', mode)
        for page_number in range(self.pdf_document.page_count):
            if self.mode == "block":
                # print('block')
                text = self.extract_text_from_pages_by_blocks(page_number)
                # print(len(text))
                
                count+=len(text)
            else:
                # print('page')
                text = self.extract_text_from_page(page_number)

            self.total_text+=text

            # call chunking here for the page data
            # create a list of chunks for a particular page
            sentence_splitter = SentenceSplitter(chunk_size=256)
            df = sentence_splitter.semantic_chunking(text)

            page_chunk_list= (df['chunked_sentence']).tolist()
            page_chunk_token_list=(df['tokens']).tolist()

            
            combined_list= []
            combined_list.append(page_chunk_list)
            combined_list.append(page_chunk_token_list)
            

            if self.mode=='page':
                extracted_data[page_number + 1] = combined_list
            else:
                # print('here')
                n= len(text)
                for i in range(n):
                    # print(i)
                    extracted_data[page_number + 1] = text[i]
        return extracted_data

    def extract_image_from_page(self):
        try :
            extracted_images= {}
            pdf_document = fitz.open(self.pdf_path)
            for page_number in range(self.pdf_document.page_count):
                page= pdf_document.load_page(page_number)
                image_list = page.get_images(full=True)

                images_base64 = []
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    images_base64.append(image_base64)

                if image_base64==None:
                    extracted_images[page_number+1]= ['none']
                else:
                    extracted_images[page_number+1]= image_base64
            return extracted_images
        except: 
            return {}


    def save_to_csv(self, data, image_data, category, keywords):
        """
        Saves text and image data to the CSV file.

        Args:
            data (dict): Dictionary containing page number and text content.
            image_data (dict): Dictionary containing page number and image data (list of values).
            category (str): Category of the data.
            keywords (list): List of keywords associated with the data.
        """

        pdf_name = os.path.basename(self.pdf_path)
        rows = []
        for page_number, combined_list in data.items():
            image_values = image_data.get(page_number, [])  # Retrieve image values, default to empty list if not found
            for i in range(len(combined_list[0])):
                rows.append([pdf_name, page_number, combined_list[0][i],combined_list[1][i], image_values, category, keywords])

        df = pd.DataFrame(rows, columns=["file_name", "Page Number", "Content", "tokens","Image_Data", "Category", "Keywords"])
        # df.to_csv(self.csv_file_name, index=False)
        self.append_to_csv(df)
    
    
    def append_to_csv(self, df):
        """Appends the given DataFrame to the output CSV file, creating it if it doesn't exist."""
        if os.path.exists(self.csv_file_name):
            mode = 'a'  # Append to existing file
        else:
            mode = 'w'  # Create a new file

        df.to_csv(self.csv_file_name, index=False, mode=mode, header=not os.path.exists(self.csv_file_name))

    @staticmethod
    def fix_text(text):
        # text fixing logic here
        # output_string = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # return output_string
        return text


    def categorise_text(self, data_str):
        file_tagger= FileTagger(api_key=api_key)
        categories=['educational', 'financial', 'human resource', 'literary', 'personal']
        
        category, keywords = file_tagger.classify_text(text=data_str, categories=categories)
        keywords_trimed=keywords[:10]
        return category, keywords_trimed

    def convert(self):
        self.open_pdf()
        data = self.extract_text_from_all_pages()
        
        image_data = self.extract_image_from_page()
        category, keywords=self.categorise_text(self.total_text)
        print('category: ',category,'\n')
        self.save_to_csv(data,image_data,category,keywords)
        self.close_pdf()


def convert_files_in_folder(folder_path, output_name='output',mode='page'):
    # Initialize the CSV file outside the loop
    output_csv = f"{output_name}.csv"
    num_files=0
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        num_files+=1
        print(file)

        if file.lower().endswith(".pdf"):
            pdf_converter = PDFToCSVConverter(file_path, output_csv, mode)
            pdf_converter.convert()

# if __name__=="__main__":
#     folder_path = r"E:\GATI AI\testing\current" 
#     convert_files_in_folder(folder_path)