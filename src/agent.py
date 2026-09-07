import os
import re
import json
import litellm
from .services import InventoryService, BillingService, KhataService, AnalyticsService

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check current available inventory stock quantity, price, and GST details for a specific item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product name or SKU to check (e.g., 'sugar', 'Maggi', 'atta', 'milk')"}
                },
                "required": ["product"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock",
            "description": "Add or update stock quantity (inward inventory) when new stock arrives from suppliers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product name or SKU"},
                    "quantity_added": {"type": "number", "description": "Quantity to add to current stock"}
                },
                "required": ["product", "quantity_added"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_report",
            "description": "Get a list of all supermarket products running low on stock (at or below minimum thresholds).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_bill_item",
            "description": "Add an item with quantity to the active customer draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product name or SKU"},
                    "quantity": {"type": "number", "description": "Quantity to bill"}
                },
                "required": ["product", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_current_draft",
            "description": "View current items, quantities, and grand total of the active draft bill.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_bill",
            "description": "Finalize and complete the active draft bill, deducting stock and recording revenue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_mode": {"type": "string", "description": "Payment mode: CASH, UPI, CARD, or KHATA"}
                },
                "required": ["payment_mode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_khata_balance",
            "description": "Check current outstanding credit balance for a customer in the Khata ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name (e.g. Ramesh, Suresh)"}
                },
                "required": ["customer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_khata_transaction",
            "description": "Record a credit purchase or customer payment in the Khata ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name"},
                    "amount": {"type": "number", "description": "Amount in INR"},
                    "transaction_type": {"type": "string", "description": "'CREDIT' if customer took goods on credit, or 'PAYMENT' if customer paid cash/UPI off their credit balance"},
                    "notes": {"type": "string", "description": "Optional notes"}
                },
                "required": ["customer_name", "amount", "transaction_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_analytics",
            "description": "Get sales analysis report including total revenue, bills issued, tax collected, and top-selling items.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

SYSTEM_PROMPT = """
You are SmartMart Assistant, a professional AI Co-Pilot for supermarket store managers.
Guidelines:
1. Maintain a clean, professional, commercial tone.
2. Execute tools immediately for user commands.
3. Keep user responses concise, clear, and formatted nicely in INR (₹).
4. Never output internal system/developer details or quota messages.
"""

CLASSIC_HELP_MENU = (
    "🛒 **SmartMart Assistant**\n\n"
    "How can I help you today? Here are some quick actions:\n"
    "• `check stock of sugar` - View stock & prices\n"
    "• `add 2 sugar to bill` - Itemize customer bill\n"
    "• `view bill` - See active bill summary\n"
    "• `finalize bill cash` - Complete customer payment\n"
    "• `add 20 maggi to stock` - Update inward inventory\n"
    "• `khata of ramesh` - Check credit balance\n\n"
    "Type `/help` to see all 6 quick menu options."
)

class AgentOrchestrator:
    def __init__(self, db_session):
        self.db = db_session

    def execute_local_intent(self, text: str, chat_id: int):
        """
        Fast, professional local intent engine.
        Handles direct keywords and store operations cleanly.
        """
        text_lower = text.strip().lower()

        # 0. Greetings / Hello / Hi
        if re.search(r'^(hi|hello|hey|greetings|start|menu)\b', text_lower):
            return (
                "👋 **Welcome to SmartMart Assistant!**\n\n"
                "I am here to help you manage your store's inventory, billing, sales, and credit ledger.\n\n"
                "💡 **Quick Keywords**:\n"
                "• `sugar` - Check stock\n"
                "• `add 2 sugar to bill` - Add to customer bill\n"
                "• `view bill` - Check current bill total\n"
                "• `khata of ramesh` - Check customer credit\n"
                "• `sales` - View revenue analytics\n\n"
                "Type `/help` for the full menu!"
            )

        # 1. Low Stock Report
        if re.search(r'\b(low\s*stock|reorder|out\s*of\s*stock)\b', text_lower):
            res = InventoryService.get_low_stock_report(self.db)
            if "message" in res:
                return f"✅ {res['message']}"
            items_str = "\n".join([f"• **{i['name']}**: {i['current_quantity']} {i['unit']} (Min Threshold: {i['min_threshold']})" for i in res['items']])
            return f"⚠️ **Low Stock Alert ({res['low_stock_count']} items)**:\n\n{items_str}"

        # 2. Sales Analytics
        if re.search(r'\b(sales|analytics|revenue|daily\s*sales)\b', text_lower):
            res = AnalyticsService.get_sales_summary(self.db)
            top_str = "\n".join([f"• {i['product']}: {i['quantity']} sold" for i in res['top_selling_items']]) if res['top_selling_items'] else "No sales recorded yet"
            return (
                f"📊 **Store Sales Summary**\n\n"
                f"• **Bills Issued**: {res['total_bills_issued']}\n"
                f"• **Total Revenue**: ₹{res['total_revenue']:.2f}\n"
                f"• **GST Collected**: ₹{res['total_tax_collected']:.2f}\n\n"
                f"🔥 **Top Selling Products**:\n{top_str}"
            )

        # 3. View Draft Bill
        if re.search(r'\b(view\s*bill|show\s*bill|current\s*bill|draft\s*bill|^bill$)\b', text_lower):
            res = BillingService.view_current_draft(self.db, chat_id)
            if "message" in res:
                return f"ℹ️ {res['message']}"
            items_str = "\n".join([f"• **{i['product_name']}**: {i['quantity']} {i['unit']} × ₹{i['unit_price']} = ₹{i['quantity']*i['unit_price']:.2f}" for i in res['items']])
            return f"🧾 **Active Draft Bill**:\n\n{items_str}\n\n💰 **Grand Total**: ₹{res['grand_total']:.2f}"

        # 4. Finalize Bill
        m_fin = re.search(r'\b(finalize|checkout|complete)\s*bill\s*(cash|upi|card|khata)?\b', text_lower) or re.search(r'\bpay\s*(cash|upi|card|khata)\b', text_lower)
        if m_fin:
            mode = m_fin.group(2) if len(m_fin.groups()) >= 2 and m_fin.group(2) else "CASH"
            res = BillingService.finalize_bill(self.db, chat_id, mode.upper())
            if "error" in res:
                return f"❌ {res['error']}"
            return f"✅ **Bill Completed**\n• Invoice: `{res['bill_number']}`\n• Grand Total: ₹{res['grand_total']:.2f}\n• Payment Mode: {res['payment_mode']}"

        # 5. Add Stock (Inward Inventory) - Explicitly requires stock/restock keywords
        if re.search(r'\b(to\s+stock|restock|replenish)\b', text_lower) or re.search(r'\bupdate\s+stock\b', text_lower):
            m_stock_add = re.search(r'\b(?:add|update|restock|replenish)\s+(?:stock\s+)?(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:packets?|kg|pack|liter|l)?\s+(?:of\s+)?([a-zA-Z0-9\s]+?)(?:\s+to\s+stock|\s+stock)?$', text_lower)
            if not m_stock_add:
                m_stock_add = re.search(r'\b(?:update\s+stock|restock)\s+([a-zA-Z0-9\s]+?)\s+(\d+(?:\.\d+)?)$', text_lower)
            if m_stock_add:
                try:
                    qty = float(m_stock_add.group(1))
                    prod_name = m_stock_add.group(2).strip().removesuffix(" to stock").removesuffix(" stock").strip()
                except (ValueError, IndexError):
                    prod_name = m_stock_add.group(1).strip()
                    qty = float(m_stock_add.group(2))
                res = InventoryService.update_stock(self.db, prod_name, qty)
                if "error" in res:
                    return f"❌ {res['error']}"
                return f"📦 **Stock Replenished**\nAdded {qty} {res['unit']} to **{res['product']}**.\nUpdated Stock: **{res['new_quantity']} {res['unit']}**"

        # 6. Sale Item / Add Item to Bill
        # Handles "add 2 sugar to bill", "bill 3 maggi", "sugar sold 2"
        m_sold = re.search(r'([a-zA-Z0-9\s]+?)\s+(?:sold|sale)\s+(\d+(?:\.\d+)?)', text_lower)
        if m_sold:
            prod_name = m_sold.group(1).strip()
            qty = float(m_sold.group(2))
            res = BillingService.add_bill_item(self.db, chat_id, prod_name, qty)
            if "error" in res:
                return f"❌ {res['error']}"
            return f"🛒 {res['message']}"

        m_bill_add = re.search(r'\b(?:add|bill|sell)\s+(\d+(?:\.\d+)?)\s*(?:kg|pack|packets?|liter|l)?\s+(?:of\s+)?([a-zA-Z0-9\s]+?)(?:\s+to\s+bill|\s+bill)?$', text_lower)
        if m_bill_add:
            qty = float(m_bill_add.group(1))
            raw_name = m_bill_add.group(2).strip()
            prod_name = re.sub(r'\s+(?:to\s+bill|bill)$', '', raw_name, flags=re.IGNORECASE).strip()
            res = BillingService.add_bill_item(self.db, chat_id, prod_name, qty)
            if "error" in res:
                return f"❌ {res['error']}"
            return f"🛒 {res['message']}"

        # 7. Khata Balance Inquiry
        m_khata = re.search(r'\b(?:khata\s+(?:of\s+)?|balance\s+(?:of\s+)?|check\s+khata\s+)([a-zA-Z\s]+)$', text_lower) or re.search(r'^([a-zA-Z]+)\s+balance$', text_lower)
        if m_khata:
            cust_name = m_khata.group(1).strip()
            res = KhataService.get_customer_balance(self.db, cust_name)
            if "error" in res:
                return f"ℹ️ {res['error']}"
            return f"📒 **Khata Ledger**: {res['customer']}\n• Credit Balance Owed: ₹{res['credit_balance']:.2f}"

        # 8. Record Khata Transaction
        m_khata_txn = re.search(r'([a-zA-Z]+)\s+(?:took|credit|took\s+on\s+credit)\s+(?:rs|inr|₹)?\s*(\d+(?:\.\d+)?)', text_lower)
        if m_khata_txn:
            cust_name = m_khata_txn.group(1).strip()
            amt = float(m_khata_txn.group(2))
            res = KhataService.record_transaction(self.db, cust_name, amt, 'CREDIT')
            return f"📒 **Credit Entry Recorded**\n• Customer: {res['customer']}\n• Credit Added: ₹{res['amount']:.2f}\n• Total Balance: ₹{res['remaining_balance']:.2f}"

        m_khata_pay = re.search(r'([a-zA-Z]+)\s+(?:paid|cleared)\s+(?:rs|inr|₹)?\s*(\d+(?:\.\d+)?)', text_lower)
        if m_khata_pay:
            cust_name = m_khata_pay.group(1).strip()
            amt = float(m_khata_pay.group(2))
            res = KhataService.record_transaction(self.db, cust_name, amt, 'PAYMENT')
            return f"✅ **Payment Recorded**\n• Customer: {res['customer']}\n• Amount Paid: ₹{res['amount']:.2f}\n• Remaining Balance: ₹{res['remaining_balance']:.2f}"

        # 9. Stock Check
        m_stock = re.search(r'\b(?:check\s+stock\s+(?:of\s+)?|stock\s+(?:of\s+)?)([a-zA-Z0-9\s]+)$', text_lower) or re.search(r'^([a-zA-Z0-9\s]+)\s+stock$', text_lower)
        if m_stock:
            prod_name = m_stock.group(1).strip()
            res = InventoryService.check_stock(self.db, prod_name)
            if "error" in res:
                return f"ℹ️ {res['error']}"
            return f"📦 **{res['name']}** ({res['sku']})\n• **Available Stock**: {res['quantity']} {res['unit']}\n• **Selling Price**: ₹{res['selling_price']:.2f}\n• **GST Rate**: {res['gst_rate']}%"

        # Direct Single-word product search (e.g. "sugar", "maggi", "milk")
        if re.match(r'^[a-zA-Z0-9\s]{2,25}$', text_lower):
            res = InventoryService.check_stock(self.db, text_lower)
            if "name" in res:
                return f"📦 **{res['name']}** ({res['sku']})\n• **Available Stock**: {res['quantity']} {res['unit']}\n• **Selling Price**: ₹{res['selling_price']:.2f}\n• **GST Rate**: {res['gst_rate']}%"

        return None

    def execute_tool(self, tool_call, chat_id):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
        
        if name == "check_stock":
            return InventoryService.check_stock(self.db, args['product'])
        elif name == "update_stock":
            return InventoryService.update_stock(self.db, args['product'], args['quantity_added'])
        elif name == "get_low_stock_report":
            return InventoryService.get_low_stock_report(self.db)
        elif name == "add_bill_item":
            return BillingService.add_bill_item(self.db, chat_id, args['product'], args['quantity'])
        elif name == "view_current_draft":
            return BillingService.view_current_draft(self.db, chat_id)
        elif name == "finalize_bill":
            return BillingService.finalize_bill(self.db, chat_id, args.get('payment_mode', 'CASH'))
        elif name == "check_khata_balance":
            return KhataService.get_customer_balance(self.db, args['customer_name'])
        elif name == "record_khata_transaction":
            return KhataService.record_transaction(self.db, args['customer_name'], args['amount'], args['transaction_type'], args.get('notes'))
        elif name == "get_sales_analytics":
            return AnalyticsService.get_sales_summary(self.db)
        return {"error": "Unknown tool"}

    def handle_message(self, user_message: str, chat_id: int):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = litellm.completion(
            model="gemini/gemini-1.5-flash",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        if message.tool_calls:
            tool_results = []
            for tool_call in message.tool_calls:
                result = self.execute_tool(tool_call, chat_id)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(result)
                })
            
            messages.append(message.model_dump())
            messages.extend(tool_results)
            
            final_response = litellm.completion(
                model="gemini/gemini-1.5-flash",
                messages=messages
            )
            return final_response.choices[0].message.content
        else:
            res_content = message.content
            return res_content if (res_content and res_content.strip()) else CLASSIC_HELP_MENU
