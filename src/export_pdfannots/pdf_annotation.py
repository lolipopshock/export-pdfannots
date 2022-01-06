from typing import List, Dict, Optional
import uuid

import pandas as pd

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage

import pdfannots
from pdfannots import Annotation, Document, AnnotationType
from pdfannots.printer.json import annot_to_dict

import edn_format
from edn_format import ImmutableDict, Keyword


def union_coordinates(coords: List[Dict]) -> Dict:
    return {
        "x1": min([coord["x1"] for coord in coords]),
        "y1": min([coord["y1"] for coord in coords]),
        "x2": max([coord["x2"] for coord in coords]),
        "y2": max([coord["y2"] for coord in coords]),
        "width": coords[0]["width"],
        "height": coords[0]["height"],
    }


def ednfy(data: Dict) -> Dict:
    """Converts a Python dict to an EDN map."""
    if isinstance(data, dict):
        return ImmutableDict({Keyword(key): ednfy(val) for key, val in data.items()})
    elif isinstance(data, tuple):
        return tuple([ednfy(ele) for ele in data])
    elif isinstance(data, list):
        return [ednfy(ele) for ele in data]
    else:
        return data


def render_logseq_note(data: Dict) -> str:
    strs = []
    for item in data:
        strs.append(f"- {item['text']}\n")
        for key, val in item.items():
            if key != "text":
                strs.append(f"  {key} {val}\n")
    return "".join(strs)


class PDFAnnotation:
    def __init__(self, pdf_path: str):
        self.page_sizes = self.load_page_sizes(pdf_path)
        self.metadata = self.load_metadata(pdf_path)
        self.annotations = self.load_annotations(pdf_path)

    @staticmethod
    def load_page_sizes(pdf_path: str) -> List[List]:
        """Loads the page mediaboxes from the PDF file."""
        with open(pdf_path, "rb") as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            page_sizes = []
            for page in PDFPage.create_pages(doc):
                page_sizes.append(page.mediabox)
        return page_sizes
    
    @staticmethod
    def load_metadata(pdf_path: str) -> Dict:
        """Loads the PDF metadata from the PDF file."""
        with open(pdf_path, "rb") as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            metadata = {}
            for key, val in doc.info[0].items():
                try:
                    metadata[key.lower()] = val.decode()
                except:
                    continue
        return metadata
    
    @staticmethod
    def load_annotations(pdf_path: str) -> Document:
        """Load PDF Annotations using the pdfannots library."""
        with open(pdf_path, "rb") as fp:
            doc = pdfannots.process_file(fp)

            # Add the uuid beforehand
            for anno in doc.iter_annots():
                anno.uuid = uuid.uuid4()

        return doc

    def create_logseq_coordinates(self, annot: Annotation) -> List[Dict]:
        """Converts PDFMiner Coordinates to the LogSeq format."""
        page_id = annot.pos.page.pageno
        _, _, w, h = self.page_sizes[page_id]

        all_coords = []
        for box in annot.boxes:
            x1, y1, x2, y2 = box.get_coords()
            all_coords.append(
                {
                    "x1": x1,
                    "y2": h - y1,  ## Note: it switches y1 and y2 for logseq readers
                    "x2": x2,
                    "y1": h - y2,
                    "width": w,
                    "height": h,
                }
            )
        return all_coords

    def export_as_logseq_edn(
        self, filename: str = None, color: str = "yellow"
    ) -> Optional[str]:
        """Exports the annotations as a LogSeq file."""
        logseq_annot_data = []

        for anno in self.annotations.iter_annots():
            if anno.subtype != AnnotationType.Highlight:
                continue
            coords = self.create_logseq_coordinates(anno)
            position = union_coordinates(coords)
            logseq_page = anno.pos.page.pageno + 1  # There's one page shift
            logseq_annot_data.append(
                {
                    "id": anno.uuid,
                    "page": logseq_page,
                    "position": {
                        "bounding": position,
                        "rects": tuple(coords),
                        "page": logseq_page,
                    },
                    "content": {"text": anno.gettext()},
                    "properties": {"color": color},
                }
            )
        logseq_annot_str = edn_format.dumps(
            {Keyword("highlights"): [ednfy(ele) for ele in logseq_annot_data]}
        )
        if filename is not None:
            with open(filename, "w") as fp:
                fp.write(logseq_annot_str)
        else:
            return logseq_annot_str

    def export_as_logseq_note(self) -> str:
        anno_data = [
            {
                "text": anno.gettext(True),
                "ls-type::": "annotation",
                "hl-page::": anno.pos.page.pageno + 1,
                "id::": anno.uuid,
            }
            for anno in self.annotations.iter_annots()
        ]
        return render_logseq_note(anno_data)

    def export_as_dict(self) -> Dict:
        return [
            annot_to_dict(self.annotations, anno, True)
            for anno in self.annotations.iter_annots()
        ]

    def export_as_markdown_note(self, title_level:int=2) -> str:
        result = []
        data = self.export_as_dict()
        _title = "######"[:title_level]
        for title, gp in pd.DataFrame(data).groupby("prior_outline", sort=False):
            result.append(
                f"{_title} {title} \n\n"
                + "\n".join([f"- {ele}" for ele in gp["text"].tolist()])
            )

        return "\n\n".join(result)