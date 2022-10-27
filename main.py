"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py
It allows you to export tables from a set of PDFs into CSVs and
download the resulting CSVs as a zip file.
"""

import os
import sys
import fnmatch
import zipfile
import subprocess
from urllib.parse import urlparse
import requests
import tabula
from documentcloud.addon import AddOn
from clouddl import grab

class Tabula(AddOn):
    """A tabula PDF table extraction Add-On for DocumentCloud"""

    def fetch_template(self, url):
        """Fetch the template from either Dropbox, Google Drive, or any public URL"""
        os.makedirs(os.path.dirname("./out/"), exist_ok=True)
        if(grab(url, "./out/")):
            for file in os.listdir('./out/'):
                if fnmatch.fnmatch(file, '*.json'):
                   template_path = os.path.join('./out/', file)
                   os.rename(template_path, os.path.join('./out/', 'template.json'))
                   return True
        else:
            parsed_url = urlparse(url)
            basename = os.path.basename(parsed_url.path)
            title, ext = os.path.splitext(basename)
            if not title:
                title = "template"
            if not ext:
                ext = "json"
            with requests.get(url, stream=True, timeout=10) as resp:
                if resp.status_code == 200:
                    with open("./out/template.json", "wb") as json_file:
                        for chunk in resp.iter_content(chunk_size=8192):
                            json_file.write(chunk)
                    return True
                else:
                    return False
           
    def template_based_extract(self, url):
        if(self.fetch_template(url)):
            with zipfile.ZipFile("export.zip", mode="w") as archive:
                for document in self.get_documents():
                    with open("file.pdf", "wb") as pdf_file:
                        pdf_file.write(document.pdf)
                    data_frame_list = tabula.read_pdf_with_template("./file.pdf", "./out/template.json") 
                    # Tabula's read_pdf_with_template() returns a list of data frames we can append to form a CSV. 
                    for data_frame in data_frame_list:
                        data_frame.to_csv(f"{document.slug}.csv", mode="a", index=False, header=False)
                    archive.write(f"{document.slug}.csv")
        else:
            self.template_less_extract()
    
    def template_less_extract(self):
        with zipfile.ZipFile("export.zip", mode="w") as archive:
            for document in self.get_documents():
                pdf_file.write(document.pdf)
                tabula.convert_into(f"{document.slug}.pdf", f"{document.slug}.csv", output_format="csv", pages="all",) 
                # Tabula's convert_into() guesses boundaries for table extraction. 
                archive.write(f"{document.slug}.csv")

    def main(self):
        """
        If a template is provided, it extracts dataframes from the PDF(s)
        using that template and appends it to a CSV for each document and returns
        a zip file of all the CSVs. If no template is provided, it guesses
        the boundaries for each file
        """
        try:
            url = self.data["url"]
        except Exception as exc:
            url = None

        if url is not None:
            self.template_based_extract(url)
        else:
            self.template_less_extract()
        
        self.upload_file(open("export.zip"))

if __name__ == "__main__":
    Tabula().main()
