import os
from pydantic import BaseModel

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.2")

    sales_file: str = os.getenv("SALES_FILE", "Sales_Active_Stores_Data.xlsb")
    po_pdf: str = os.getenv("PO_PDF", "Purchase_Order_2025-12-12.pdf")
    pi_pdf: str = os.getenv("PI_PDF", "Proforma_Invoice_2025-12-12.pdf")

    # If you want to store parsed plans/results (optional)
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
