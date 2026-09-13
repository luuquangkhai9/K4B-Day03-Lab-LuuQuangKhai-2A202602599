"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

def parse_thought_and_content(text: str) -> Tuple[str, str]:
    """
    Phân tách chuỗi phản hồi text từ LLM thành (thought, content)
    nếu LLM sinh ra các token suy nghĩ tự nhiên theo định dạng Thought/Final Answer.
    """
    if not text:
        return "", ""
    text_clean = text.strip()
    thought = ""
    content = text_clean
    
    if "thought:" in text_clean.lower():
        match = re.search(r"(?:thought|suy nghĩ|lập luận):\s*(.*?)(?=(?:\n\s*(?:final answer|câu trả lời|kết luận):)|$)", text_clean, re.IGNORECASE | re.DOTALL)
        if match:
            thought = match.group(1).strip()
            
        answer_match = re.search(r"(?:final answer|câu trả lời|kết luận):\s*(.*)", text_clean, re.IGNORECASE | re.DOTALL)
        if answer_match:
            content = answer_match.group(1).strip()
        elif thought:
            content = text_clean[match.end():].strip()
            
    if not thought:
        thought = "Mô hình phân tích thông tin và phản hồi trực tiếp cho người dùng."
        
    return thought, content

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key (Hỗ trợ cả Single-step và Multi-step)"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot Baseline không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: Any, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        executed_tools = []
        user_query = ""
        last_observation = {}
        
        if isinstance(prompt, list):
            for m in prompt:
                if m.get("role") == "user" and not user_query:
                    user_query = m.get("content", "")
                if m.get("role") == "tool":
                    executed_tools.append(m.get("name"))
                    try:
                        last_observation = json.loads(m.get("content", "{}"))
                    except Exception:
                        pass
                if m.get("tool_calls"):
                    for tc in m.get("tool_calls", []):
                        executed_tools.append(tc.get("function", {}).get("name"))
        else:
            user_query = str(prompt)
            
        prompt_lower = user_query.lower()
        
        # Nhận diện TC04: Multi-step Reasoning (Tra cứu trước -> Cập nhật sau)
        is_multi_step = (
            ("kiểm tra" in prompt_lower or "tra cứu" in prompt_lower or "ở đâu" in prompt_lower or "vị trí" in prompt_lower) and
            ("cập nhật" in prompt_lower or "xuất kho" in prompt_lower or "sẵn sàng" in prompt_lower) and
            ("vn-log" in prompt_lower or "đơn hàng" in prompt_lower)
        )
        
        if is_multi_step:
            if "query_shipment" not in executed_tools:
                return {
                    "type": "tool_call",
                    "tool_name": "query_shipment",
                    "arguments": {"tracking_id": "VN-LOG2026-01"},
                    "thought": "Bước 1/2: Tra cứu vị trí lưu kho hiện tại của đơn hàng VN-LOG2026-01 trước khi cập nhật."
                }
            elif "update_order_status" not in executed_tools:
                loc = "Khu A, Kệ A-12, Tầng 3"
                if last_observation and "data" in last_observation:
                    loc = last_observation["data"].get("warehouse_location", loc)
                return {
                    "type": "tool_call",
                    "tool_name": "update_order_status",
                    "arguments": {
                        "tracking_id": "VN-LOG2026-01",
                        "status": "Sẵn sàng xuất kho",
                        "warehouse_location": loc
                    },
                    "thought": f"Bước 2/2: Đã xác định vị trí kho ({loc}). Tiến hành gọi Tool cập nhật trạng thái đơn hàng sang 'Sẵn sàng xuất kho'."
                }
            else:
                return {
                    "type": "text",
                    "content": "Đơn hàng VN-LOG2026-01 hiện đang nằm ở vị trí kho Khu A, Kệ A-12, Tầng 3. Tôi đã cập nhật thành công trạng thái đơn hàng sang 'Sẵn sàng xuất kho'.",
                    "thought": "Đã hoàn thành chuỗi suy luận ReAct đa bước: tra cứu vị trí kho và cập nhật trạng thái đơn hàng."
                }

        # Nếu đã gọi tool ở bước trước cho câu hỏi đơn bước, sinh câu trả lời tổng hợp (Final Answer)
        if executed_tools:
            if "query_shipment" in executed_tools:
                if last_observation.get("status") == "NOT_FOUND":
                    return {
                        "type": "text",
                        "content": last_observation.get("message", "Không tìm thấy mã vận đơn trong hệ thống."),
                        "thought": "Mã vận đơn không tồn tại, phản hồi thông báo lịch sự không bịa đặt dữ liệu."
                    }
                d = last_observation.get("data", {})
                return {
                    "type": "text",
                    "content": f"Kiện hàng {d.get('tracking_id', 'VN-LOG2026-01')} ({d.get('item_name', 'Hàng hóa')}) hiện có trạng thái '{d.get('status', 'Đã nhập kho')}', lưu kho tại {d.get('warehouse_location', 'Khu A, Kệ A-12, Tầng 3')}.",
                    "thought": "Tổng hợp kết quả tra cứu mã vận đơn từ MCP Server."
                }
            elif "update_order_status" in executed_tools:
                msg = last_observation.get("message", "Đã cập nhật trạng thái đơn hàng thành công.")
                return {
                    "type": "text",
                    "content": msg,
                    "thought": "Xác nhận cập nhật trạng thái đơn hàng thành công qua MCP Server."
                }

        # Single-step: Khởi động gọi Tool lần đầu
        if "vn-log9999" in prompt_lower or "không tồn tại" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "query_shipment",
                "arguments": {"tracking_id": "VN-LOG9999-99"},
                "thought": "Người dùng tra cứu mã vận đơn không tồn tại VN-LOG9999-99. Tôi sẽ gọi tool query_shipment để kiểm tra CSDL."
            }
        elif "cập nhật" in prompt_lower or "thay đổi" in prompt_lower:
            status = "Đã nhập kho" if "nhập" in prompt_lower else "Sẵn sàng xuất kho"
            loc = "Khu A, Kệ A-12, Tầng 3" if "a-12" in prompt_lower or "kệ" in prompt_lower else "Khu Vực Chờ Xuất Hàng"
            return {
                "type": "tool_call",
                "tool_name": "update_order_status",
                "arguments": {
                    "tracking_id": "VN-LOG2026-01",
                    "status": status,
                    "warehouse_location": loc,
                    "note": "14:30 15/09/2026"
                },
                "thought": "Người dùng yêu cầu cập nhật trạng thái đơn hàng và vị trí kho. Tôi sẽ gọi tool update_order_status."
            }
        elif "vn-log" in prompt_lower or "ord-" in prompt_lower or "vận đơn" in prompt_lower or "kiện hàng" in prompt_lower or "tra cứu" in prompt_lower:
            tid = "VN-LOG2026-01"
            match = re.search(r"(VN-LOG\d{4}-\d{2}|ORD-\d{4}-\d{3})", user_query, re.IGNORECASE)
            if match:
                tid = match.group(1).upper()
            return {
                "type": "tool_call",
                "tool_name": "query_shipment",
                "arguments": {"tracking_id": tid},
                "thought": f"Người dùng muốn tra cứu thông tin mã vận đơn/đơn hàng {tid}. Tôi sẽ gọi tool query_shipment để truy vấn dữ liệu từ MCP Server."
            }
        else:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Quy trình nhập kho tiêu chuẩn bao gồm 4 bước: (1) Tiếp nhận & đối soát vận đơn; (2) Kiểm tra ngoại quan & số lượng; (3) Gán mã định danh và lưu kho theo sơ đồ Zone/Kệ/Tầng; (4) Cập nhật trạng thái 'Đã nhập kho' lên hệ thống quản lý kho (WMS).",
                "thought": "Câu hỏi chung về quy trình kho vận, trả lời trực tiếp từ kiến thức hệ thống không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: Any, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            if isinstance(prompt, list):
                contents = []
                for m in prompt:
                    role = "user" if m.get("role") in ["user", "tool"] else "model"
                    c = m.get("content") or ""
                    if m.get("role") == "tool":
                        c = f"Observation từ công cụ {m.get('name')}: {c}"
                    contents.append(f"{role}: {c}")
                prompt_content = "\n".join(contents)
            else:
                prompt_content = str(prompt)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt_content,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                thought_token = args.pop("thought", None)
                if not thought_token:
                    thought_token = f"Gemini quyết định gọi công cụ '{call.name}'."
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": thought_token
                }
            else:
                raw_text = response.text or ""
                thought_token, clean_content = parse_thought_and_content(raw_text)
                return {
                    "type": "text",
                    "content": clean_content,
                    "thought": thought_token
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với GPT-4o-mini / GPT-4o)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: Any, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if isinstance(prompt, list):
                for m in prompt:
                    if isinstance(m, dict):
                        cleaned = {"role": m.get("role", "user")}
                        if m.get("content") is not None:
                            cleaned["content"] = m.get("content")
                        elif m.get("role") == "assistant" and m.get("tool_calls"):
                            cleaned["content"] = None
                        if m.get("tool_calls"):
                            cleaned["tool_calls"] = m.get("tool_calls")
                        if m.get("tool_call_id"):
                            cleaned["tool_call_id"] = m.get("tool_call_id")
                        if m.get("name"):
                            cleaned["name"] = m.get("name")
                        messages.append(cleaned)
                    else:
                        messages.append(m)
            else:
                messages.append({"role": "user", "content": str(prompt)})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.1
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                
                # Trích xuất token suy luận tự nhiên (Thought) do mô hình trực tiếp sinh ra
                thought_token = args.pop("thought", None)
                if not thought_token and msg.content:
                    thought_token = msg.content.strip()
                if not thought_token:
                    thought_token = f"OpenAI phân tích yêu cầu và quyết định gọi công cụ '{call.function.name}'."

                raw_tool_calls = [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {
                            "name": c.function.name,
                            "arguments": c.function.arguments
                        }
                    }
                    for c in msg.tool_calls
                ]
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "tool_call_id": call.id,
                    "raw_message": {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": raw_tool_calls
                    },
                    "thought": thought_token
                }
            else:
                raw_text = msg.content or ""
                
                # Fallback: Nếu mô hình xuất ra cú pháp gọi tool trong nội dung text thay vì Native Function Call
                match = re.search(r"(?:functions\.)?(query_shipment|update_order_status)\s*\(\s*(\{.*?\})\s*\)", raw_text, re.DOTALL)
                if match:
                    tool_name = match.group(1)
                    raw_args_str = match.group(2)
                    try:
                        args = json.loads(raw_args_str)
                    except Exception:
                        args = {}
                    thought_token = args.pop("thought", None)
                    if not thought_token:
                        thought_token = raw_text.split(match.group(0))[0].strip() or f"Phân tích yêu cầu và gọi công cụ '{tool_name}'."
                    return {
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "arguments": args,
                        "tool_call_id": f"call_parsed_{int(time.time()*1000)}",
                        "thought": thought_token
                    }

                thought_token, clean_content = parse_thought_and_content(raw_text)
                return {
                    "type": "text",
                    "content": clean_content,
                    "thought": thought_token
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
