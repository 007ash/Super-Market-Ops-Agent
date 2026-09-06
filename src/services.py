import json
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func
from .models import Product, Bill, BillItem, Customer, KhataTransaction, InventoryTransaction, BillDraft

class InventoryService:
    @staticmethod
    def get_product_by_name(db: Session, name: str):
        return db.execute(select(Product).filter(Product.normalized_name.ilike(f"%{name.lower()}%"))).scalars().first()

    @staticmethod
    def get_product_by_sku(db: Session, sku: str):
        return db.execute(select(Product).filter(Product.sku == sku)).scalars().first()
        
    @staticmethod
    def check_stock(db: Session, product_name: str):
        prod = InventoryService.get_product_by_name(db, product_name)
        if not prod:
            return {"error": f"Product '{product_name}' not found in catalog."}
        return {
            "sku": prod.sku,
            "name": prod.name,
            "quantity": float(prod.quantity),
            "unit": prod.unit,
            "selling_price": float(prod.selling_price),
            "gst_rate": float(prod.gst_rate)
        }

class BillingService:
    @staticmethod
    def add_bill_item(db: Session, chat_id: int, product_name: str, quantity: float):
        prod = InventoryService.get_product_by_name(db, product_name)
        if not prod:
            return {"error": f"Product '{product_name}' not found."}
        if prod.quantity < quantity:
            return {"error": f"Insufficient stock. Available: {prod.quantity} {prod.unit}"}
            
        draft = db.get(BillDraft, chat_id)
        if draft:
            items = json.loads(draft.draft_json)
        else:
            items = []
            
        # Check if already in draft
        found = False
        for item in items:
            if item['product_id'] == prod.id:
                item['quantity'] += quantity
                found = True
                break
        
        if not found:
            items.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "quantity": quantity,
                "unit": prod.unit,
                "unit_price": float(prod.selling_price),
                "gst_rate": float(prod.gst_rate)
            })
            
        if draft:
            draft.draft_json = json.dumps(items)
        else:
            draft = BillDraft(chat_id=chat_id, draft_json=json.dumps(items))
            db.add(draft)
        db.commit()
        return {"success": True, "message": f"Added {quantity} of {prod.name} to draft bill."}

    @staticmethod
    def view_current_draft(db: Session, chat_id: int):
        draft = db.get(BillDraft, chat_id)
        if not draft:
            return {"message": "No active draft bill."}
        
        items = json.loads(draft.draft_json)
        total = sum(item['quantity'] * item['unit_price'] for item in items)
        return {"items": items, "grand_total": total}

    @staticmethod
    def finalize_bill(db: Session, chat_id: int, payment_mode: str):
        draft = db.get(BillDraft, chat_id)
        if not draft:
            return {"error": "No draft bill to finalize."}
        items = json.loads(draft.draft_json)
        if not items:
            return {"error": "Draft bill is empty."}
            
        grand_total = Decimal('0')
        total_taxable = Decimal('0')
        total_tax = Decimal('0')
        
        bill = Bill(
            bill_number=f"KP-{chat_id}-{func.now()}",
            chat_id=chat_id,
            payment_mode=payment_mode,
            status='COMPLETED',
            total_taxable=0, total_cgst=0, total_sgst=0, total_tax=0, grand_total=0
        )
        db.add(bill)
        db.flush() # get ID
        
        for item in items:
            qty = Decimal(str(item['quantity']))
            price = Decimal(str(item['unit_price']))
            gst_rate = Decimal(str(item['gst_rate']))
            
            # Simplified tax calc
            total_amount = qty * price
            tax_amount = total_amount * gst_rate / (100 + gst_rate)
            taxable_val = total_amount - tax_amount
            
            grand_total += total_amount
            total_tax += tax_amount
            total_taxable += taxable_val
            
            bi = BillItem(
                bill_id=bill.id,
                product_id=item['product_id'],
                product_name=item['product_name'],
                unit=item['unit'],
                quantity=qty,
                unit_price=price,
                mrp=price,
                gst_rate=gst_rate,
                taxable_value=taxable_val,
                cgst_amount=tax_amount/2,
                sgst_amount=tax_amount/2,
                total_amount=total_amount,
                hsn_code="0000"
            )
            db.add(bi)
            
            # Decrement stock
            db.execute(update(Product).where(Product.id == item['product_id']).values(quantity=Product.quantity - qty))
            
        bill.total_taxable = total_taxable
        bill.total_tax = total_tax
        bill.total_cgst = total_tax / 2
        bill.total_sgst = total_tax / 2
        bill.grand_total = grand_total
        
        db.delete(draft)
        db.commit()
        return {"success": True, "message": f"Bill {bill.id} finalized for {grand_total} via {payment_mode}."}
        
class KhataService:
    @staticmethod
    def get_customer_balance(db: Session, customer_name: str):
        cust = db.execute(select(Customer).filter(Customer.normalized_name.ilike(f"%{customer_name.lower()}%"))).scalars().first()
        if not cust:
            return {"error": f"Customer '{customer_name}' not found."}
        return {"customer": cust.name, "balance": float(cust.current_credit_balance)}

