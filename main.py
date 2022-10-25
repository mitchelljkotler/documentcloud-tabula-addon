"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py
It allows you to export tables from a set of PDFs into CSVs and
download the resulting CSVs as a zip file.
"""

import os
import sys
import zipfile
import subprocess
from urllib.parse import urlparse

import requests
import tabula

from documentcloud.addon import AddOn
from clouddl import grab
from clouddl import DROPBOX_URL, GDRIVE_URL


class Tabula(AddOn):
    """A tabula Add-On for DocumentCloud"""

    def fetch_files(self, url):
        """Fetch the files from either Dropbox, Google Drive, or any public URL"""
        self.set_message("Downloading the files...")

        os.makedirs(os.path.dirname("./out/"), exist_ok=True)
        cloud_urls = [DROPBOX_URL, GDRIVE_URL]
        if any(cloud_url in url for cloud_url in cloud_urls):
            grab(url, "./out/")
            rename_file = "cd out; mv * template.json"
            subprocess.call(rename_file, shell=True)

        else:
            parsed_url = urlparse(url)
            basename = os.path.basename(parsed_url.path)
            title, ext = os.path.splitext(basename)
            if not title:
                title = "template"
            if not ext:
                ext = "json"
            with requests.get(url, stream=True, timeout=10) as resp:
                resp.raise_for_status()
                with open("./out/template.json", "wb") as json_file:
                    for chunk in resp.iter_content(chunk_size=8192):
                        json_file.write(chunk)

    def main(self):
        """If a template is provided, it extracts dataframes from the PDF(s)
        using that template and appends it to a CSV for each document and returns
        a zip file of all the CSVs. If no template is provided, it guesses
        the boundaries for each file"""
        with zipfile.ZipFile("export.zip", mode="w") as archive:
            url = self.data["url"]
            self.fetch_files(url)
            for document in self.get_documents():
                if url is not None: #the if branch gets executed if a template is provided
                    with open("file.pdf", "wb") as pdf_file:
                        pdf_file.write(document.pdf)
                    data_frame_list = tabula.read_pdf_with_template("./file.pdf", "./out/template.json") 
                    # Tabula's read_pdf_with_template() returns a list of data frames we can append to form a CSV. 
                    for data_frame in data_frame_list:
                        data_frame.to_csv(
                            f"{document.slug}.csv", mode="a", index=False, header=False
                        )
                else: #the else branch gets executed if no template is provided. 
                    with open(f"{document.slug}.pdf", "wb") as pdf_file: 
                        pdf_file.write(document.pdf)
                    tabula.convert_into(f"{document.slug}.pdf", f"{document.slug}.csv", output_format="csv", pages="all",) 
                    # Tabula's convert_into() guesses boundaries for table extraction. 
                archive.write(f"{document.slug}.csv")
        self.upload_file(open("export.zip"))


if __name__ == "__main__":
    Tabula().main()
