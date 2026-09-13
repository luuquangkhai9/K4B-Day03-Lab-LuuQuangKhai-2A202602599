"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Chủ đề: Trợ lý Đơn hàng & Kho vận (Supply Chain Agent).
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu mã vận đơn, vị trí lưu kho và trạng thái đơn hàng
    {
        "name": "query_shipment",
        "description": "Tra cứu thông tin mã vận đơn, vị trí lưu kho và tình trạng đơn hàng trong hệ thống kho vận Supply Chain.",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Lập luận suy nghĩ (Thought): Diễn giải token suy nghĩ tự nhiên của bạn — giải thích lý do vì sao gọi công cụ này và bạn dự định làm gì với kết quả tra cứu được."
                },
                "tracking_id": {
                    "type": "string",
                    "description": "Mã vận đơn hoặc mã đơn hàng cần tra cứu (ví dụ: 'VN-LOG2026-01')"
                }
            },
            "required": ["tracking_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # Tool 2: Cập nhật trạng thái đơn hàng và vị trí lưu kho
    # --------------------------------------------------------------------------
    {
        "name": "update_order_status",
        "description": "Cập nhật trạng thái đơn hàng và vị trí lưu kho trong hệ thống quản lý kho vận (WMS).",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Lập luận suy nghĩ (Thought): Diễn giải token suy nghĩ tự nhiên của bạn — giải thích cơ sở hoặc kết quả quan sát trước đó để đưa ra quyết định cập nhật trạng thái này."
                },
                "tracking_id": {
                    "type": "string",
                    "description": "Mã vận đơn hoặc mã đơn hàng cần cập nhật (ví dụ: 'VN-LOG2026-01')"
                },
                "status": {
                    "type": "string",
                    "description": "Trạng thái mới của đơn hàng (ví dụ: 'Đã nhập kho', 'Đang phân loại', 'Sẵn sàng xuất kho', 'Đang giao')"
                },
                "warehouse_location": {
                    "type": "string",
                    "description": "Vị trí lưu kho mới của kiện hàng (ví dụ: 'Kệ A-12, Tầng 3')"
                },
                "note": {
                    "type": "string",
                    "description": "Ghi chú bổ sung hoặc thời gian thực hiện cập nhật (ví dụ: '14:30 15/09/2026')"
                }
            },
            "required": ["tracking_id", "status"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

import copy

INITIAL_DATABASE = {
    "VN-LOG2026-01": {
        "tracking_id": "VN-LOG2026-01",
        "order_id": "ORD-2026-001",
        "item_name": "Linh kiện Cảm biến LiDAR & Bộ điều khiển",
        "quantity": 10,
        "sender": "VinFast Hải Phòng",
        "recipient": "Đại học VinUni, Gia Lâm, Hà Nội",
        "status": "Đã nhập kho",
        "warehouse_location": "Khu A, Kệ A-12, Tầng 3",
        "last_updated": "14:30 15/09/2026"
    },
    "VN-LOG2026-02": {
        "tracking_id": "VN-LOG2026-02",
        "order_id": "ORD-2026-002",
        "item_name": "Thiết bị Edge Computing Jetson Orin",
        "quantity": 5,
        "sender": "Trung tâm R&D VinAI Hà Nội",
        "recipient": "Kho Vận VinUni Smart Campus",
        "status": "Chờ xuất kho",
        "warehouse_location": "Khu B, Kệ B-05, Tầng 1",
        "last_updated": "09:15 15/09/2026"
    },
    "VN-LOG2026-03": {
        "tracking_id": "VN-LOG2026-03",
        "order_id": "ORD-2026-003",
        "item_name": "Pin Lithium-ion Thể rắn (Solid-State Battery Pack)",
        "quantity": 24,
        "sender": "Tổ hợp Sản xuất VinES Hà Tĩnh",
        "recipient": "Xưởng Lắp Ráp Xe Điện VinFast Hải Phòng",
        "status": "Đang lưu kho tiêu chuẩn",
        "warehouse_location": "Khu C (Kho Hàng Chống Cháy), Kệ C-01, Tầng 1",
        "last_updated": "08:00 16/09/2026"
    },
    "VN-LOG2026-04": {
        "tracking_id": "VN-LOG2026-04",
        "order_id": "ORD-2026-004",
        "item_name": "Cụm Màn hình HUD Thông minh & Bộ hiển thị kính lái AI",
        "quantity": 50,
        "sender": "VinSmart Khu Công Nghệ Cao Hòa Lạc",
        "recipient": "Trung tâm Nghiên cứu Xe Tự hành VinAI",
        "status": "Đang kiểm định chất lượng (QC)",
        "warehouse_location": "Khu Kiểm Định QC, Bàn Kỹ Thuật B-02",
        "last_updated": "10:20 16/09/2026"
    },
    "VN-LOG2026-05": {
        "tracking_id": "VN-LOG2026-05",
        "order_id": "ORD-2026-005",
        "item_name": "Module Ăng-ten Radar Milimet 77GHz cho ADAS",
        "quantity": 120,
        "sender": "Tập đoàn Bosch Việt Nam (KCN Long Thành)",
        "recipient": "Kho Trung Chuyển Logistics Gia Lâm",
        "status": "Đã phân loại",
        "warehouse_location": "Khu A, Kệ A-08, Tầng 2",
        "last_updated": "11:45 16/09/2026"
    },
    "VN-LOG2026-06": {
        "tracking_id": "VN-LOG2026-06",
        "order_id": "ORD-2026-006",
        "item_name": "Robot Vận chuyển Tự hành AMR-500 Smart Logistics",
        "quantity": 3,
        "sender": "Viện Nghiên cứu Trí tuệ Nhân tạo VinAI",
        "recipient": "Smart Warehouse Lab Đại học VinUni",
        "status": "Sẵn sàng bàn giao",
        "warehouse_location": "Khu Hàng Quá Khổ D, Gian D-03, Tầng 1",
        "last_updated": "13:10 16/09/2026"
    },
    "VN-LOG2026-07": {
        "tracking_id": "VN-LOG2026-07",
        "order_id": "ORD-2026-007",
        "item_name": "Máy Chủ Siêu tính toán AI NVIDIA DGX H100",
        "quantity": 2,
        "sender": "Trung tâm Dữ liệu Siêu máy tính Viettel IDC",
        "recipient": "Viện Nghiên cứu Đổi mới Sáng tạo VinUni",
        "status": "Lưu kho an ninh cao",
        "warehouse_location": "Khu An Ninh S, Tủ Rack S-09 (Kho Khóa Điện Tử)",
        "last_updated": "15:00 16/09/2026"
    },
    "VN-LOG2026-08": {
        "tracking_id": "VN-LOG2026-08",
        "order_id": "ORD-2026-008",
        "item_name": "Cuộn Cáp Quang Tốc độ cao 400Gbps & Bộ Thu Phát QSFP-DD",
        "quantity": 200,
        "sender": "VNPT Technology Hà Nội",
        "recipient": "Phòng Thí nghiệm Mạng Không dây VinUni",
        "status": "Đã nhập kho",
        "warehouse_location": "Khu B, Kệ B-14, Tầng 4",
        "last_updated": "16:30 16/09/2026"
    },
    "VN-LOG2026-09": {
        "tracking_id": "VN-LOG2026-09",
        "order_id": "ORD-2026-009",
        "item_name": "Hệ thống Cảm biến Môi trường Kho vận IoT (Nhiệt độ & Độ ẩm)",
        "quantity": 35,
        "sender": "BKAV Hardware Solution Cầu Giấy",
        "recipient": "Ban Quản lý Chuỗi Cung ứng Smart Logistics",
        "status": "Chờ xuất kho",
        "warehouse_location": "Khu A, Kệ A-03, Tầng 1",
        "last_updated": "17:15 16/09/2026"
    },
    "VN-LOG2026-10": {
        "tracking_id": "VN-LOG2026-10",
        "order_id": "ORD-2026-010",
        "item_name": "Vật liệu Tản nhiệt Graphene Chuyên dụng cho Pin Xe Điện",
        "quantity": 80,
        "sender": "Khoa Hóa học Đại học Khoa học Tự nhiên ĐHQGHN",
        "recipient": "Xưởng Sản xuất Pin VinES Hải Phòng",
        "status": "Đang lưu kho lạnh (Cold Storage)",
        "warehouse_location": "Kho Lạnh L, Ngăn L-02 (Dải nhiệt 2°C - 8°C)",
        "last_updated": "08:45 17/09/2026"
    }
}

MOCK_DATABASE = copy.deepcopy(INITIAL_DATABASE)


def reset_mock_database():
    """Khôi phục CSDL kho vận về trạng thái ban đầu"""
    global MOCK_DATABASE
    MOCK_DATABASE.clear()
    MOCK_DATABASE.update(copy.deepcopy(INITIAL_DATABASE))


def execute_query_shipment(tracking_id: str = "", **kwargs) -> str:
    """Thực thi tra cứu vận đơn và vị trí lưu kho theo mã vận đơn hoặc mã đơn hàng"""
    target_id = (tracking_id or kwargs.get("order_id") or kwargs.get("student_id") or "").strip().upper()
    
    # 1. Tra cứu trực tiếp theo key chính (tracking_id)
    if target_id in MOCK_DATABASE:
        shipment = MOCK_DATABASE[target_id]
        return json.dumps({
            "status": "SUCCESS",
            "tracking_id": target_id,
            "data": shipment,
            "message": f"Tìm thấy kiện hàng {target_id}: Mặt hàng '{shipment.get('item_name', '')}', Trạng thái '{shipment.get('status', '')}', Vị trí lưu kho '{shipment.get('warehouse_location', '')}', Số lượng: {shipment.get('quantity', 0)}."
        }, ensure_ascii=False)
        
    # 2. Tra cứu linh hoạt theo order_id (ví dụ: ORD-2026-003) hoặc tìm kiếm theo mã
    if target_id:
        for tid, data in MOCK_DATABASE.items():
            if data.get("order_id", "").upper() == target_id:
                return json.dumps({
                    "status": "SUCCESS",
                    "tracking_id": tid,
                    "data": data,
                    "message": f"Tìm thấy kiện hàng {tid} (Mã đơn: {data.get('order_id')}): Mặt hàng '{data.get('item_name', '')}', Trạng thái '{data.get('status', '')}', Vị trí lưu kho '{data.get('warehouse_location', '')}', Số lượng: {data.get('quantity', 0)}."
                }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy dữ liệu vận đơn có mã '{target_id}' trong hệ thống kho vận."
    }, ensure_ascii=False)


def execute_update_order_status(tracking_id: str = "", status: str = "", warehouse_location: str = "", note: str = "", **kwargs) -> str:
    """Thực thi cập nhật trạng thái đơn hàng và vị trí lưu kho"""
    target_id = (tracking_id or kwargs.get("order_id") or kwargs.get("student_id") or "").strip().upper()
    target_status = status or kwargs.get("datetime_str") or "Đã cập nhật"
    
    # Tìm key tương ứng trong MOCK_DATABASE
    key = target_id
    if target_id not in MOCK_DATABASE:
        for tid, data in MOCK_DATABASE.items():
            if target_id and data.get("order_id", "").upper() == target_id:
                key = tid
                break
    
    if key in MOCK_DATABASE:
        MOCK_DATABASE[key]["status"] = target_status
        if warehouse_location:
            MOCK_DATABASE[key]["warehouse_location"] = warehouse_location
        if note:
            MOCK_DATABASE[key]["last_updated"] = note
        loc = MOCK_DATABASE[key].get("warehouse_location", warehouse_location)
        return json.dumps({
            "status": "SUCCESS",
            "update_id": f"UP-{key}-99",
            "tracking_id": key,
            "order_status": target_status,
            "warehouse_location": loc,
            "message": f"Cập nhật thành công đơn hàng {key}: Trạng thái '{target_status}', vị trí lưu kho '{loc}'."
        }, ensure_ascii=False)
    else:
        # Tự động tạo bản ghi mới nếu mã chưa có trong hệ thống
        MOCK_DATABASE[key] = {
            "tracking_id": key,
            "status": target_status,
            "warehouse_location": warehouse_location or "Khu Chờ Phân Loại",
            "last_updated": note or "14:30 15/09/2026"
        }
        return json.dumps({
            "status": "SUCCESS",
            "update_id": f"UP-{key}-99",
            "tracking_id": key,
            "order_status": target_status,
            "warehouse_location": warehouse_location or "Khu Chờ Phân Loại",
            "message": f"Cập nhật thành công đơn hàng {key}: Trạng thái '{target_status}', vị trí lưu kho '{warehouse_location or 'Khu Chờ Phân Loại'}'."
        }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "query_shipment": execute_query_shipment,
    "update_order_status": execute_update_order_status,
    # Hỗ trợ alias linh hoạt cho LLM và tương thích ngược
    "warehouse_lookup": execute_query_shipment,
    "track_shipment": execute_query_shipment,
    "academic_query": execute_query_shipment,
    "schedule_appointment": execute_update_order_status
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
