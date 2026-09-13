# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Lưu Quang Khải  
> **Mã Sinh Viên / Mã Học viên:** 2A202602599 
> **Chủ đề Lựa chọn:** *Trợ lý Đơn hàng & Kho vận (Supply Chain Agent):* Tra cứu mã vận đơn, vị trí lưu kho và cập nhật trạng thái đơn hàng.  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **5** / 5 | Bài toán đòi hỏi chuỗi suy luận logic nhiều bước tuần tự: (1) Tiếp nhận và trích xuất mã vận đơn/mã kiện hàng từ yêu cầu tự nhiên; (2) Suy luận tra cứu vị trí kho (Khu vực/Kệ/Tầng); (3) Đối chiếu điều kiện nghiệp vụ kho vận (tính sẵn sàng, hợp lệ); (4) Ra quyết định thực thi cập nhật trạng thái đơn và tổng hợp thông tin phản hồi. |
| **2. Tool Interaction** | **5** / 5 | Hệ thống không thể dùng tri thức tĩnh có sẵn (parametric knowledge) mà bắt buộc phải kết nối 2 chiều với hệ thống WMS/ERP qua MCP Server: Tool đọc (`query_shipment` / `get_inventory_location`) để lấy dữ liệu thời gian thực và Tool ghi (`update_order_status`) để cập nhật trạng thái vào cơ sở dữ liệu. |
| **3. Dynamic Decision** | **5** / 5 | Nhánh xử lý tiếp theo phụ thuộc hoàn toàn vào kết quả quan sát (Observation) từ Tool ở bước trước: Nếu mã vận đơn không tồn tại thì xử lý ngoại lệ; Nếu đơn hàng đang bị khóa/hư hại (Hold/Damaged) thì chuyển luồng thông báo sự cố; Nếu hợp lệ thì tiến hành cập nhật trạng thái mới. |
| **4. Long Horizon Goal** | **4** / 5 | Agent cần duy trì mục tiêu xử lý đơn hàng xuyên suốt chuỗi hội thoại đa lượt (multi-turn): từ tra cứu vị trí, hỏi xác nhận thông tin bổ sung từ nhân sự kho (Human-in-the-loop), đến thực thi cập nhật và lưu vết audit log thành công. |
| **TỔNG ĐIỂM AGENTIC FIT** | **19 / 20** | *Kết luận: 19/20 >> 12/20. Bài toán cực kỳ phù hợp để phát triển ReAct Agent tích hợp MCP Server.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Kiểm tra xem đơn hàng VN-LOG2026-01 hiện đang nằm ở vị trí kho nào, sau đó cập nhật trạng thái đơn hàng sang 'Sẵn sàng xuất kho'.",
    "action_type": "TOOL_EXECUTION",
    "thought": "Tôi cần tra cứu thông tin đơn hàng VN-LOG2026-01 để biết vị trí kho hiện tại trước khi cập nhật trạng thái đơn hàng.",
    "tool_name": "query_shipment",
    "arguments": {
      "tracking_id": "VN-LOG2026-01"
    },
    "observation": {
      "status": "SUCCESS",
      "tracking_id": "VN-LOG2026-01",
      "data": {
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
      "message": "Tìm thấy kiện hàng VN-LOG2026-01: Mặt hàng 'Linh kiện Cảm biến LiDAR & Bộ điều khiển', Trạng thái 'Đã nhập kho', Vị trí lưu kho 'Khu A, Kệ A-12, Tầng 3', Số lượng: 10."
    },
    "latency_ms": 1870.53
  },
  {
    "step": 2,
    "query": "Kiểm tra xem đơn hàng VN-LOG2026-01 hiện đang nằm ở vị trí kho nào, sau đó cập nhật trạng thái đơn hàng sang 'Sẵn sàng xuất kho'.",
    "action_type": "TOOL_EXECUTION",
    "thought": "Đơn hàng VN-LOG2026-01 hiện đang ở vị trí 'Khu A, Kệ A-12, Tầng 3' và có trạng thái 'Đã nhập kho'. Tôi sẽ cập nhật trạng thái đơn hàng sang 'Sẵn sàng xuất kho'.",
    "tool_name": "update_order_status",
    "arguments": {
      "tracking_id": "VN-LOG2026-01",
      "status": "Sẵn sàng xuất kho",
      "warehouse_location": "Khu A, Kệ A-12, Tầng 3",
      "note": "Cập nhật trạng thái lúc 14:30 15/09/2026"
    },
    "observation": {
      "status": "SUCCESS",
      "update_id": "UP-VN-LOG2026-01-99",
      "tracking_id": "VN-LOG2026-01",
      "order_status": "Sẵn sàng xuất kho",
      "warehouse_location": "Khu A, Kệ A-12, Tầng 3",
      "message": "Cập nhật thành công đơn hàng VN-LOG2026-01: Trạng thái 'Sẵn sàng xuất kho', vị trí lưu kho 'Khu A, Kệ A-12, Tầng 3'."
    },
    "latency_ms": 1438.23
  },
  {
    "step": 3,
    "query": "Kiểm tra xem đơn hàng VN-LOG2026-01 hiện đang nằm ở vị trí kho nào, sau đó cập nhật trạng thái đơn hàng sang 'Sẵn sàng xuất kho'.",
    "action_type": "FINAL_ANSWER",
    "thought": "Mô hình phân tích thông tin và phản hồi trực tiếp cho người dùng.",
    "output": "Tôi đã kiểm tra thông tin đơn hàng VN-LOG2026-01 và nhận được kết quả như sau:\n\n- **Mặt hàng**: Linh kiện Cảm biến LiDAR & Bộ điều khiển\n- **Số lượng**: 10\n- **Người gửi**: VinFast Hải Phòng\n- **Người nhận**: Đại học VinUni, Gia Lâm, Hà Nội\n- **Trạng thái hiện tại**: Đã nhập kho\n- **Vị trí lưu kho**: Khu A, Kệ A-12, Tầng 3\n\nSau đó, tôi đã cập nhật trạng thái đơn hàng sang **'Sẵn sàng xuất kho'**.\n\nThông tin cập nhật thành công như sau:\n- **Trạng thái mới**: Sẵn sàng xuất kho\n- **Vị trí lưu kho**: Khu A, Kệ A-12, Tầng 3\n\nNếu bạn cần thêm thông tin gì khác, hãy cho tôi biết!",
    "latency_ms": 2327.98
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (OpenAI `gpt-4o-mini`).
- **Tổng số Test Cases đã chạy thành công:** **5** / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** **5** lượt (bao gồm chuỗi 2 Tool gọi tuần tự trong TC04 đa bước: `query_shipment` ➔ `update_order_status`).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
