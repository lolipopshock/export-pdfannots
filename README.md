# `Export-PDFAnnots`

## What is this library?

[pdfannots](https://github.com/0xabu/pdfannots) is a great tool that extracts annotations from PDF files.
However, it provides limited support for migrating the annotation data to other software or other formats.
`Export-PDFAnnots` tries to bridge this gap by providing additional 

## Use Cases

- Export PDF Annotations to LogSeq: 
    ```python
    from export_pdfannots import LogSeqFolderHandler
    logseq_folder = LogSeqFolderHandler("logseq_folder)
    logseq_folder.add_pdf_and_annotations("path/to/pdf_file.pdf")
    ```

- Export PDF Annotations to a Notion database: 
    ```python
    from export_pdfannots import NotionDfHandler
    # Assume you've set the notion-api-key in the environment variable NOTION_API_KEY
    # e.g., os.environ['NOTION_API_KEY'] = "your-api-key"
    notion_dfh = NotionDfHandler("notion_database_url")
    notion_dfh.add_annotations("path/to/pdf_file.pdf")
    ```

## TODOs

- [ ] Add support for Hypothesis