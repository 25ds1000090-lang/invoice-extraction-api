import os
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI(title="Invoice Intelligence API")

class LineItem(BaseModel):
    sku: str
    quantity: int
    unit_price: int

class ExtractedInvoice(BaseModel):
    vendor: str = Field(description="The biller's proper name, exactly as written.")
    currency: str = Field(description="ISO 4217 code (USD, EUR, GBP, INR, JPY, etc.).")
    total_amount: int = Field(description="Integer in main unit without symbols or separators.")
    invoice_date: str = Field(description="Date formatted as YYYY-MM-DD.")
    due_in_days: int = Field(description="Integer number of days.")
    is_paid: bool = Field(description="True if paid, False otherwise.")
    priority: str = Field(description="One of: low, normal, high, urgent.")
    contact_email: str = Field(description="Lowercased email address.")
    line_items: List[LineItem] = Field(description="Array of item objects.")
    item_count: int = Field(description="Number of items in line_items.")

class InvoiceRequest(BaseModel):
    document_id: str
    text: str
    schema: Dict[str, Any] | None = None

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/extract-invoice")
def extract_invoice(req: InvoiceRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not configured in Render."
        )

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Extract structured invoice fields from this document text:\n\n{req.text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedInvoice,
                temperature=0.0,
            ),
        )

        extracted_obj = response.parsed
        if extracted_obj is None:
            extracted_obj = ExtractedInvoice.model_validate_json(response.text)

        data = extracted_obj.model_dump()

        if data.get("contact_email"):
            data["contact_email"] = data["contact_email"].lower()
        data["item_count"] = len(data.get("line_items", []))

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
