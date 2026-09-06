import json
import litellm
from .services import InventoryService, BillingService, KhataService

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check current available inventory stock quantity, price, and GST details for a specific item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Product name or SKU to check (e.g., 'sugar', 'Maggi', 'atta')"}
                },
                "required": ["product"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_bill_item",
            "description": "Add an item with quantity to the active draft customer bill.",
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
            "description": "View current items and grand total of the draft bill.",
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
            "description": "Finalize and complete the current draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_mode": {"type": "string", "description": "Payment mode (CASH, UPI, CARD, KHATA)"}
                },
                "required": ["payment_mode"]
            }
        }
    }
]

class AgentOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        
    def execute_tool(self, tool_call, chat_id):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if name == "check_stock":
            return InventoryService.check_stock(self.db, args['product'])
        elif name == "add_bill_item":
            return BillingService.add_bill_item(self.db, chat_id, args['product'], args['quantity'])
        elif name == "view_current_draft":
            return BillingService.view_current_draft(self.db, chat_id)
        elif name == "finalize_bill":
            return BillingService.finalize_bill(self.db, chat_id, args.get('payment_mode', 'CASH'))
        return {"error": "Unknown tool"}

    async def handle_message(self, user_message: str, chat_id: int):
        messages = [
            {"role": "system", "content": "You are AI_smart_mart, an AI agent running a supermarket. Use tools to manage inventory, billing, and khata."},
            {"role": "user", "content": user_message}
        ]
        
        response = await litellm.acompletion(
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
            
            final_response = await litellm.acompletion(
                model="gemini/gemini-1.5-flash",
                messages=messages
            )
            return final_response.choices[0].message.content
        else:
            return message.content

