"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py

It allows you to export tables from a set of PDFs and allows you to download the results as a zip file. 
"""

import os
import tabula
import pandas
import requests
import zipfile
from urllib.parse import urlparse
from documentcloud.addon import AddOn
import lootdl
from lootdl import DROPBOX_URL, GDRIVE_URL, MEDIAFIRE_URL, WETRANSFER_URL

class Tabula(AddOn):
    """A tabula Add-On for DocumentCloud"""

    def fetch_files(self, url):
        """Fetch the files from either a cloud share link or any public URL"""
        self.set_message("Downloading the files...")

        os.makedirs(os.path.dirname("./out/"), exist_ok=True)
        cloud_urls = [DROPBOX_URL, GDRIVE_URL, MEDIAFIRE_URL, WETRANSFER_URL]
        if any(cloud_url in url for cloud_url in cloud_urls):
            # surpress output during lootdl download to avoid leaking
            # private information
            stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            lootdl.grab(url, "./out/")
            # restore stdout
            sys.stdout = stdout
        else:
            parsed_url = urlparse(url)
            basename = os.path.basename(parsed_url.path)
            title, ext = os.path.splitext(basename)
            if not title:
                title = "template"
            if not ext:
                ext = "json"
            with requests.get(url, stream=True) as resp:
                resp.raise_for_status()
                with open(f"{title}.{ext}", "wb") as json_file:
                    for chunk in resp.iter_content(chunk_size=8192):
                        json_file.write(chunk)
                 
    def main(self):
        with zipfile.ZipFile("export.zip", mode="w") as archive:
            for document in self.get_documents():
                url = self.data['url']
                if url is not None: 
                    self.fetch_files(url)
                    pdf_name = f"{document.title}.pdf"
            
                    with open("file.pdf", "wb") as pdf_file:
                        pdf_file.write(document.pdf)
                    data_frame_list = tabula.read_pdf_with_template("./file.pdf", "template.json")
                    for data_frame in data_frame_list:
                        data_frame.to_csv(f"{document.slug}.csv", mode='a', index=False, header=False)
                else: 
                    with open(f"{document.slug}.pdf", "wb") as pdf_file:
                        pdf_file.write(document.pdf)
                    tabula.convert_into(f"{document.slug}.pdf", f"{document.slug}.csv", output_format="csv", pages="all")
                archive.write(f"{document.slug}.csv")
        self.upload_file(open("export.zip"))
if __name__ == "__main__":
    Tabula().main()
