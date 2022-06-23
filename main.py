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
        with open(f"{document.slug}.pdf", "w") as pdf_file:
            pdf_file.write(document.pdf)

        tabula.convert_into(
            f"{document.slug}.pdf", f"{document.slug}.csv", output_format="csv", pages="all"
        )

        with open(f"{document.slug}.csv") as csv_file:
            self.upload_file(csv_file)


if __name__ == "__main__":
    Tabula().main()
