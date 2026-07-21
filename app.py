import os
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import openai

app = FastAPI(title="Invoice Intelligence API")


# Define the strict output Pydantic model for Structured Outputs
class LineItem(BaseModel):
    sku: str
    quantity: int
    unit_price: int


class ExtractedInvoice(BaseModel):
    vendor: str = Field(description="The biller's proper name, exactly as written.")
    currency: str = Field(description="ISO 4217 code (e.g. USD, EUR, GBP, INR, JPY).")
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
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not configured in Render."
        )

    client = openai.OpenAI(api_key=api_key)

    try:
        # Request OpenAI Structured Output to match the strict JSON shape
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a structured data extractor. Extract invoice details from text. "
                        "Normalize currency to ISO 4217, total_amount to a plain integer, invoice_date to YYYY-MM-DD, "
                        "contact_email to lower case, and compute item_count to match length of line_items."
                    ),
                },
                {"role": "user", "content": f"Document ID: {req.document_id}\n\nText:\n{req.text}"},
            ],
            response_format=ExtractedInvoice,
            temperature=0.0,
        )

        data = completion.choices[0].message.parsed.model_dump()
        
        # Ensure email is lowercased and item_count matches
        if data.get("contact_email"):
            data["contact_email"] = data["contact_email"].lower()
        data["item_count"] = len(data.get("line_items", []))

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
