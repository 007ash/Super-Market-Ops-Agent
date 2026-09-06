from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    sku: str
    name: str
    unit: str
    is_packaged: bool
    cost_price: Decimal
    selling_price: Decimal
    mrp: Decimal
    quantity: Decimal = Decimal('0')
    reorder_level: Decimal = Decimal('5.0')
    gst_rate: Decimal
    hsn_code: str
    description: Optional[str] = None

class ProductSchema(ProductBase):
    id: int
    active: bool
    model_config = ConfigDict(from_attributes=True)

class BillItemSchema(BaseModel):
    product_id: int
    product_name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    mrp: Decimal
    gst_rate: Decimal
    hsn_code: str
    taxable_value: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal

class BillSchema(BaseModel):
    id: int
    bill_number: str
    chat_id: Optional[int]
    total_taxable: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_tax: Decimal
    grand_total: Decimal
    payment_mode: str
    status: str
    created_at: datetime
    items: List[BillItemSchema] = []
    model_config = ConfigDict(from_attributes=True)

class CustomerSchema(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    current_credit_balance: Decimal
    model_config = ConfigDict(from_attributes=True)
