"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py

It attempts to convert tables from PDFs to CSVs
"""

import os.path
import tabula
import pandas
import requests
from documentcloud.addon import AddOn


class Tabula(AddOn):
    """A tabula Add-On for DocumentCloud"""

    def main(self):
        
        for document in self.get_documents():
            url = self.data['url']
            if url is not None: 
                with open("template.json", "wb") as template_file:
                    resp = requests.get(url)
                    template_file.write(resp.content)
                pdf_name = f"{document.title}.pdf"
            
                with open("file.pdf", "wb") as pdf_file:
                    pdf_file.write(document.pdf)
                data_frame_list = tabula.read_pdf_with_template("./file.pdf", "template.json")
                for data_frame in data_frame_list:
                    data_frame.to_csv(f"{document.slug}.csv", mode='a', index=False, header=False)
                with open(f"{document.slug}.csv") as csv_file:
                    self.upload_file(csv_file)

            else: 
                with open(f"{document.slug}.pdf", "wb") as pdf_file:
                    pdf_file.write(document.pdf)
                tabula.convert_into(f"{document.slug}.pdf", f"{document.slug}.csv", output_format="csv", pages="all")
                with open(f"{document.slug}.csv") as csv_file:
                    self.upload_file(csv_file)

if __name__ == "__main__":
    Tabula().main()
