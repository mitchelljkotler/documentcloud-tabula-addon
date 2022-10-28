
# DocumentCloud Tabula Add-On

This is an add-on for [DocumentCloud](https://documentcloud.org) which wraps the [tabula-py](https://github.com/chezou/tabula-py) library.

It allows you to extract and export tables from a set of PDFs into CSVs and download the resulting CSVs as a zip file.

You can provide a public Google Drive or Dropbox link to a template generated from the [Tabula Desktop Application](https://tabula.technology)
to run against the documents. 

If no template is provided, the add-on will try to guess the boundaries of the tables within the file with varying degrees of success. 
