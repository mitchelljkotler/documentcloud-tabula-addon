"""
This is an Add-On for DocumentCloud which wraps the tabula-py library
https://github.com/chezou/tabula-py

It attempts to convert tables from PDFs to CSVs
"""

import tabula
from documentcloud.addon import AddOn


class Tabula(AddOn):
    """A tabula Add-On for DocumentCloud"""

    def main(self):

        document = self.client.documents.get(self.documents[0])
        tabula.convert_into(
            document.pdf_url, f"{document.slug}.csv", output_format="csv", pages="all"
        )

        with open(f"{document.slug}.csv") as file_:
            self.upload_file(file_)


if __name__ == "__main__":
    Tabula().main()
