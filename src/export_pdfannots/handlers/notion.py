from typing import List, Dict, Optional
import os

import pandas as pd
import notion_df

notion_df.config(os.getenv("NOTION_API_KEY", None))
notion_df.pandas()

from export_pdfannots.pdf_annotation import PDFAnnotation

class NotionDfHandler:
    def __init__(self, notion_database_url:str):
        self.notion_database_url = notion_database_url
    
    def add_annotations(self,
        pdf_path: str,
        pdf_anno: Optional[PDFAnnotation] = None):
        
        if pdf_anno is None:
            pdf_anno = PDFAnnotation(pdf_path)
            
        df = pd.DataFrame(pdf_anno.export_as_dict())
        df = df[['text', 'page', 'type', 'start_xy', 'prior_outline', 'created']]
        df.columns = [ele.lower() for ele in df.columns]
        df['book'] = pdf_anno.metadata.get('title', None)
        
        df['hash'] = df['text'].apply(hash)
        notion_df = pd.read_notion(self.notion_database_url)
        notion_df['hash'] = notion_df['text'].apply(hash)
        
        uploading_df = df[ ~df['hash'].isin(notion_df['hash']) ].drop(columns=['hash'])
        uploading_df.to_notion(self.notion_database_url)