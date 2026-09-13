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
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85
      }
    },
    "latency_ms": 120.5
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** ___ / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
