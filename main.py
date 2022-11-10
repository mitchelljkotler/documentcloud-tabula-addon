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
import requests
import tabula
from documentcloud.addon import AddOn
from clouddl import grab

class Tabula(AddOn):
    """A tabula PDF table extraction Add-On for DocumentCloud"""

    def fetch_template(self, url):
        """Fetch the template from either Dropbox or Google Drive"""
        os.makedirs(os.path.dirname("./out/"), exist_ok=True)
        downloaded = grab(url, "./out/")
        if downloaded:
            for file in os.listdir("./out/"):
                if fnmatch.fnmatch(file, "*.json"):
                    template_path = os.path.join("./out/", file)
                    os.rename(template_path, os.path.join("./out/", "template.json"))
                    return True
        else:
            resp = requests.get(url)
            if resp.status_code == 200:
                with open("./out/template.json", "w") as json_file:
                    json_file.write(resp.text)
                    try:
                        json.loads(resp.text)
                    except ValueError as e:
                        self.set_message("No valid JSON tabula template was found in the URL provided, exiting...")
                        sys.exit(1)
                return True
            
        self.set_message("No valid JSON tabula template was found in the URL provided, exiting...")
        sys.exit(1)

    def template_based_extract(self, url):
        """This will run tabula's extraction with a template you provided"""
        self.fetch_template(url)
        with zipfile.ZipFile("export.zip", mode="w") as archive:
            for document in self.get_documents():
                with open("file.pdf", "wb") as pdf_file:
                    pdf_file.write(document.pdf)
                data_frame_list = tabula.read_pdf_with_template("./file.pdf", "./out/template.json")
                # Tabula's read_pdf_with_template() returns data frame list to append to CSV
                for data_frame in data_frame_list:
                    data_frame.to_csv(f"{document.slug}.csv", mode="a", index=False, header=False)
                archive.write(f"{document.slug}.csv")
                    
    def template_less_extract(self):
        """If no template is provided, tabula will guess the boundaries of the tables"""
        with zipfile.ZipFile("export.zip", mode="w") as archive:
            for document in self.get_documents():
                with open("file.pdf", "wb") as pdf_file:
                    pdf_file.write(document.pdf)
                tabula.convert_into(
                    "file.pdf",
                    f"{document.slug}.csv",
                    output_format="csv",
                    pages="all",
                )
                # Tabula's convert_into() guesses boundaries for table extraction.
                archive.write(f"{document.slug}.csv")

    def main(self):
        """
        If a template is provided, it extracts dataframes from the PDF(s)
        using that template and appends it to a CSV for each document and returns
        a zip file of all the CSVs. If no template is provided, it guesses
        the boundaries for each file
        """

        url = self.data.get("url")
        if url is None:
            self.template_less_extract()
        else:
            self.template_based_extract(url)
        self.upload_file(open("export.zip"))

if __name__ == "__main__":
    Tabula().main()
