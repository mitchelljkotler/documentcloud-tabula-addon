"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py
It allows you to export tables from a set of PDFs into CSVs and
download the resulting CSVs as a zip file.
"""

import fnmatch
import os
import sys
import zipfile

import requests
from documentcloud.addon import SoftTimeOutAddOn

import tabula
from clouddl import grab


class Tabula(SoftTimeOutAddOn):
    """A tabula PDF table extraction Add-On for DocumentCloud"""

    soft_time_limit = 5

    def __init__(self):
        super().__init__()
        self.timed_out = False

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
        with zipfile.ZipFile("export.zip", mode="a") as archive:
            for document in self.get_documents():
                print("document", document.title)
                with open("file.pdf", "wb") as pdf_file:
                    pdf_file.write(document.pdf)
                data_frame_list = tabula.read_pdf_with_template("./file.pdf", "./out/template.json")
                # Tabula's read_pdf_with_template() returns data frame list to append to CSV
                for data_frame in data_frame_list:
                    data_frame.to_csv(f"{document.slug}.csv", mode="a", index=False, header=False)
                archive.write(f"{document.slug}.csv")
                    
    def template_less_extract(self):
        """If no template is provided, tabula will guess the boundaries of the tables"""
        with zipfile.ZipFile("export.zip", mode="a") as archive:
            for document in self.get_documents():
                print("document", document.title)
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

    def cleanup(self):
        """Move export.zip into the cache directory so it is available upon restart"""
        print("cleanup")
        os.renames("export.zip", "cache/export.zip")
        self.timed_out = True

    def restore(self):
        """If we have a cache zip file, move it to the current directory
        to add more files"""
        print("restore")
        if os.path.exists("cache/export.zip"):
            print("restoring!")
            os.renames("cache/export.zip", "export.zip")

    def main(self):
        """
        If a template is provided, it extracts dataframes from the PDF(s)
        using that template and appends it to a CSV for each document and returns
        a zip file of all the CSVs. If no template is provided, it guesses
        the boundaries for each file
        """

        self.restore()

        url = self.data.get("url")
        if url is None:
            self.template_less_extract()
        else:
            self.template_based_extract(url)

        if not self.timed_out:
            self.upload_file(open("export.zip"))

if __name__ == "__main__":
    Tabula().main()
