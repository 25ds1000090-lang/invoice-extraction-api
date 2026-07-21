from os import environ
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

app = FastAPI(title="Invoice Extraction API")
client = openai.OpenAI(api_key=environ.get("OPENAI_API_KEY"))


class InvoiceRequest(BaseModel):
    document_id: str
    text: str
    schema: Dict[str, Any] | None = None


@app.get("/")
def health_check():
    return {"status": "online"}


@app.post("/extract-invoice")
def extract_invoice(req: InvoiceRequest):
    try:
        prompt = f"Extract structured invoice fields from this text:\n\n{req.text}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract invoice fields strictly. Normalize currency to ISO symbols, dates to YYYY-MM-DD, and total amounts to integers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))