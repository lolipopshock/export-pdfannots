from typing import List, Dict, Optional
import os
import shutil

from export_pdfannots.pdf_annotation import PDFAnnotation

DEFAULT_ASSETS_FOLDER = "assets"
DEFAULT_PAGES_FOLDER = "pages"
PAPER_PAGE_PREFIX = "hls__"
PAPER_PAGE_TEMPLATE = r"""file:: [{pdf_name}](file://{pdf_target})
file-path:: file://{pdf_target}

{logseq_note}
"""


class LogSeqFolderHandler:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def add_pdf_and_annotations(
        self,
        pdf_path: str,
        pdf_anno: Optional[PDFAnnotation] = None,
        asset_folder: str = DEFAULT_ASSETS_FOLDER,
        pages_folder: str = DEFAULT_PAGES_FOLDER,
        symlink_paper: bool = False,
    ):
        """Add a PDF file and its annotations to the LogSeq folder.

        Args:
            pdf_path (str):
                The pdf_file path.
            pdf_anno (Optional[PDFAnnotation], optional):
                The extracted PDFAnnotations. If not provided, it will
                run pdfannots extraction again to load the annotations.
            asset_folder (str, optional):
                The asset folder to copy the pdf file to.
                Defaults to DEFAULT_ASSETS_FOLDER.
            pages_folder (str, optional):
                The pages folder to create the PDF data page.
                Defaults to DEFAULT_PAGES_FOLDER.
            symlink_paper (bool, optional):
                Whether create a symlink for the paper.
        """

        os.makedirs(f"{self.path}/{DEFAULT_ASSETS_FOLDER}", exist_ok=True)
        os.makedirs(f"{self.path}/{asset_folder}", exist_ok=True)
        os.makedirs(f"{self.path}/{pages_folder}", exist_ok=True)

        # STEP1: Copy or symlink the paper
        pdf_name = os.path.basename(pdf_path)
        pdf_target = f"{self.path}/{asset_folder}/{pdf_name}"
        if not os.path.exists(pdf_target):
            if not symlink_paper:
                shutil.copy2(pdf_path, pdf_target)
            else:
                os.symlink(pdf_path, pdf_target)

        # STEP2: Convert the annotations
        if pdf_anno is None:
            pdf_anno = PDFAnnotation(pdf_path)
        edn_target = (
            f"{self.path}/{DEFAULT_ASSETS_FOLDER}/{pdf_name.replace('.pdf', '.edn')}"
        )
        pdf_anno.export_as_logseq_edn(edn_target)

        # STEP3: Create a paper page with all annotations
        papge_page_target = f"{self.path}/{pages_folder}/{PAPER_PAGE_PREFIX}{pdf_name.replace('.pdf', '.md')}"
        logseq_note = pdf_anno.export_as_logseq_note()
        with open(papge_page_target, "w") as fp:
            fp.write(
                PAPER_PAGE_TEMPLATE.format(
                    pdf_name=pdf_name,
                    pdf_target=pdf_target,
                    logseq_note=logseq_note,
                )
            )
