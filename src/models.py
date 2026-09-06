from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Boolean, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()

def now_utc():
    return datetime.now(timezone.utc)

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    is_packaged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=0.000, index=True)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=5.000)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    hsn_code: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class InventoryTransaction(Base):
    __tablename__ = 'inventory_transactions'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('products.id'), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False) # STOCK_IN, SALE, RETURN, ADJUSTMENT
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    current_credit_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class KhataTransaction(Base):
    __tablename__ = 'khata_transactions'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('customers.id'), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False) # CREDIT_GIVEN, PAYMENT_RECEIVED, ADJUSTMENT
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bill_id: Mapped[str] = mapped_column(String(64), nullable=True)
    payment_mode: Mapped[str] = mapped_column(String(32), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

class Bill(Base):
    __tablename__ = 'bills'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bill_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('customers.id'), nullable=True)
    total_taxable: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cgst: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_sgst: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(32), nullable=False) # CASH, UPI, CARD, KHATA
    payment_reference: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='COMPLETED') # DRAFT, COMPLETED, CANCELLED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    
    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

class BillItem(Base):
    __tablename__ = 'bill_items'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bill_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('bills.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('products.id'), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hsn_code: Mapped[str] = mapped_column(String(32), nullable=False)
    taxable_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    bill = relationship("Bill", back_populates="items")

class BillDraft(Base):
    __tablename__ = 'bill_drafts'

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    draft_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class OwnerPreference(Base):
    __tablename__ = 'owner_preferences'

    pref_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    pref_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class ProcessedMessage(Base):
    __tablename__ = 'processed_messages'

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
