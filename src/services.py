import json
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func
from .models import Product, Bill, BillItem, Customer, KhataTransaction, InventoryTransaction, BillDraft

class InventoryService:
    @staticmethod
    def get_product_by_name(db: Session, name: str):
        # Try exact/ilike match first
        prod = db.execute(select(Product).filter(Product.normalized_name.ilike(f"%{name.lower()}%"))).scalars().first()
        if prod:
            return prod
        # Fallback to fuzzy search (pg_trgm)
        return db.execute(select(Product).order_by(func.similarity(Product.normalized_name, name.lower()).desc())).scalars().first()

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

    @staticmethod
    def update_stock(db: Session, product_name: str, quantity_added: float):
        prod = InventoryService.get_product_by_name(db, product_name)
        if not prod:
            return {"error": f"Product '{product_name}' not found."}
        
        new_qty = Decimal(str(prod.quantity)) + Decimal(str(quantity_added))
        prod.quantity = new_qty
        
        # Record inventory transaction
        txn = InventoryTransaction(
            product_id=prod.id,
            transaction_type='STOCK_IN',
            quantity_change=Decimal(str(quantity_added)),
            balance_after=new_qty,
            remarks='Stock Restock'
        )
        db.add(txn)
        db.commit()
        return {"success": True, "product": prod.name, "new_quantity": float(new_qty), "unit": prod.unit}

    @staticmethod
    def get_low_stock_report(db: Session):
        products = db.execute(select(Product).filter(Product.quantity <= Product.reorder_level)).scalars().all()
        if not products:
            return {"message": "All products are well stocked above minimum thresholds!"}
        
        items = []
        for p in products:
            items.append({
                "name": p.name,
                "current_quantity": float(p.quantity),
                "min_threshold": float(p.reorder_level),
                "unit": p.unit
            })
        return {"low_stock_count": len(items), "items": items}

    @staticmethod
    def get_all_inventory(db: Session):
        products = db.execute(select(Product).filter(Product.active == True).order_by(Product.name)).scalars().all()
        if not products:
            return {"message": "No active products found in inventory.", "items": []}
        
        items = []
        for p in products:
            items.append({
                "sku": p.sku,
                "name": p.name,
                "quantity": float(p.quantity),
                "unit": p.unit,
                "selling_price": float(p.selling_price)
            })
        return {"total_products": len(items), "items": items}


class BillingService:
    @staticmethod
    def add_bill_item(db: Session, chat_id: int, product_name: str, quantity: float):
        prod = InventoryService.get_product_by_name(db, product_name)
        if not prod:
            return {"error": f"Product '{product_name}' not found."}
        if prod.quantity < quantity:
            return {"error": f"Insufficient stock for {prod.name}. Available: {prod.quantity} {prod.unit}"}
            
        draft = db.get(BillDraft, chat_id)
        if draft:
            items = json.loads(draft.draft_json)
        else:
            items = []
            
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
        return {"success": True, "message": f"Added {quantity} {prod.unit} of {prod.name} to draft bill."}

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
            return {"error": "No active draft bill to finalize."}
        items = json.loads(draft.draft_json)
        if not items:
            return {"error": "Draft bill is empty."}
            
        grand_total = Decimal('0')
        total_taxable = Decimal('0')
        total_tax = Decimal('0')
        
        bill = Bill(
            bill_number=f"BILL-{chat_id}-{int(func.extract('epoch', func.now()))}",
            chat_id=chat_id,
            payment_mode=payment_mode,
            status='COMPLETED',
            total_taxable=0, total_cgst=0, total_sgst=0, total_tax=0, grand_total=0
        )
        db.add(bill)
        db.flush()
        
        for item in items:
            qty = Decimal(str(item['quantity']))
            price = Decimal(str(item['unit_price']))
            gst_rate = Decimal(str(item['gst_rate']))
            
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
            db.execute(update(Product).where(Product.id == item['product_id']).values(quantity=Product.quantity - qty))
            
        bill.total_taxable = total_taxable
        bill.total_tax = total_tax
        bill.total_cgst = total_tax / 2
        bill.total_sgst = total_tax / 2
        bill.grand_total = grand_total
        
        db.delete(draft)
        db.commit()
        return {"success": True, "bill_number": bill.bill_number, "grand_total": float(grand_total), "payment_mode": payment_mode}

class KhataService:
    @staticmethod
    def get_customer_balance(db: Session, customer_name: str):
        cust = db.execute(select(Customer).filter(Customer.normalized_name.ilike(f"%{customer_name.lower()}%"))).scalars().first()
        if not cust:
            return {"error": f"Customer '{customer_name}' not found."}
        return {"customer": cust.name, "phone": cust.phone, "credit_balance": float(cust.current_credit_balance)}

    @staticmethod
    def record_transaction(db: Session, customer_name: str, amount: float, txn_type: str, notes: str = None):
        # txn_type: 'CREDIT' (added to balance owed) or 'PAYMENT' (customer paid off credit)
        cust = db.execute(select(Customer).filter(Customer.normalized_name.ilike(f"%{customer_name.lower()}%"))).scalars().first()
        if not cust:
            # Create new customer if not found
            cust = Customer(
                name=customer_name.title(),
                normalized_name=customer_name.lower(),
                current_credit_balance=Decimal('0')
            )
            db.add(cust)
            db.flush()
        
        amt = Decimal(str(amount))
        if txn_type.upper() == 'CREDIT':
            cust.current_credit_balance += amt
        elif txn_type.upper() == 'PAYMENT':
            cust.current_credit_balance -= amt
        
        txn = KhataTransaction(
            customer_id=cust.id,
            transaction_type=txn_type.upper(),
            amount=amt,
            balance_after=cust.current_credit_balance,
            notes=notes or f"Recorded {txn_type.upper()}"
        )
        db.add(txn)
        db.commit()
        return {
            "success": True,
            "customer": cust.name,
            "transaction_type": txn_type.upper(),
            "amount": float(amt),
            "remaining_balance": float(cust.current_credit_balance)
        }

class AnalyticsService:
    @staticmethod
    def get_sales_summary(db: Session):
        total_bills = db.execute(select(func.count(Bill.id))).scalar() or 0
        total_revenue = db.execute(select(func.sum(Bill.grand_total))).scalar() or Decimal('0')
        total_tax = db.execute(select(func.sum(Bill.total_tax))).scalar() or Decimal('0')
        
        # Get top 5 sold items
        top_items_query = (
            select(BillItem.product_name, func.sum(BillItem.quantity).label('total_qty'))
            .group_by(BillItem.product_name)
            .order_by(func.sum(BillItem.quantity).desc())
            .limit(5)
        )
        top_items = db.execute(top_items_query).all()
        top_items_list = [{"product": row[0], "quantity": float(row[1])} for row in top_items]

        return {
            "total_bills_issued": total_bills,
            "total_revenue": float(total_revenue),
            "total_tax_collected": float(total_tax),
            "top_selling_items": top_items_list
        }
