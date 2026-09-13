"""
🌐 WEB CHAT & REACT AGENT VISUALIZER (SUPPLY CHAIN AGENT)
Giao diện Web Chat trực quan hiển thị luồng ReAct (Thought -> Action -> Observation)
Sử dụng Python built-in http.server, không phụ thuộc thư viện ngoài.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Thêm thư mục hiện tại vào sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPSupplyChainServer
from providers import get_llm_provider
from prompts import MAX_ITERATIONS, REACT_AGENT_SYSTEM_PROMPT
from tools import MOCK_DATABASE, TOOLS_SCHEMA, reset_mock_database
from app import run_react_agent, save_waterfall_trace

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi" class="h-full">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Supply Chain ReAct Agent - Chat & Visualizer</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    /* Tùy chỉnh thanh cuộn */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }
    .step-active { animation: pulse-glow 1.5s infinite; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 h-full flex flex-col font-sans antialiased overflow-hidden">

  <!-- TOP NAVBAR -->
  <header class="bg-slate-900/90 border-b border-slate-800 px-6 py-3 flex items-center justify-between shrink-0">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
        <i class="fa-solid fa-boxes-packing text-lg"></i>
      </div>
      <div>
        <h1 class="text-base font-bold text-white flex items-center gap-2">
          Trợ lý Đơn hàng & Kho vận (Supply Chain Agent)
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            ReAct Level 3 • MCP Connected
          </span>
        </h1>
        <p class="text-xs text-slate-400">Tra cứu mã vận đơn, sơ đồ lưu kho và cập nhật trạng thái đơn hàng thời gian thực</p>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      <div id="llm-status-badge" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-xs">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-emerald-300 font-medium font-mono">LLM: OpenAI (gpt-4o-mini) - LIVE</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="text-slate-300 font-medium" id="server-status">MCP Server: 2 Tools</span>
      </div>
      <a href="/pipeline_infographic.jpg" target="_blank" class="px-3 py-1.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 hover:text-white text-xs font-medium border border-indigo-800/50 transition flex items-center gap-1.5">
        <i class="fa-solid fa-image"></i> Xem Infographic Pipeline
      </a>
      <button onclick="clearChat()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition flex items-center gap-1.5">
        <i class="fa-solid fa-rotate-left"></i> Làm mới Chat
      </button>
    </div>
  </header>

  <!-- MAIN WORKSPACE: 2 COLUMNS -->
  <main class="flex-1 flex overflow-hidden">
    
    <!-- LEFT COLUMN: CHAT INTERFACE (60%) -->
    <section class="w-7/12 border-r border-slate-800 flex flex-col bg-slate-900/40">
      
      <!-- QUICK PROMPTS CHIPS -->
      <div class="px-5 py-2.5 border-b border-slate-800/80 bg-slate-900/30 flex items-center gap-2 overflow-x-auto whitespace-nowrap text-xs">
        <span class="text-slate-400 font-medium shrink-0 flex items-center gap-1">
          <i class="fa-solid fa-bolt text-amber-400"></i> Test Cases:
        </span>
        <button onclick="setPrompt('TC01')" class="px-2.5 py-1 rounded-md bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition">
          TC01: Quy trình nhập kho
        </button>
        <button onclick="setPrompt('TC02')" class="px-2.5 py-1 rounded-md bg-blue-950/60 hover:bg-blue-900/60 text-blue-300 hover:text-blue-100 border border-blue-800/50 transition">
          TC02: Tra cứu VN-LOG2026-01
        </button>
        <button onclick="setPrompt('TC03')" class="px-2.5 py-1 rounded-md bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 hover:text-emerald-100 border border-emerald-800/50 transition">
          TC03: Cập nhật Đã nhập kho
        </button>
        <button onclick="setPrompt('TC04')" class="px-2.5 py-1 rounded-md bg-purple-950/60 hover:bg-purple-900/60 text-purple-300 hover:text-purple-100 border border-purple-800/50 transition">
          TC04: ReAct đa bước (Xuất kho)
        </button>
        <button onclick="setPrompt('TC05')" class="px-2.5 py-1 rounded-md bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 hover:text-rose-100 border border-rose-800/50 transition">
          TC05: Mã lỗi VN-LOG9999-99
        </button>
        <button onclick="setPrompt('EX01')" class="px-2.5 py-1 rounded-md bg-amber-950/60 hover:bg-amber-900/60 text-amber-300 hover:text-amber-100 border border-amber-800/50 transition">
          Pin thể rắn (VN-LOG2026-03)
        </button>
        <button onclick="setPrompt('EX02')" class="px-2.5 py-1 rounded-md bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 hover:text-cyan-100 border border-cyan-800/50 transition">
          Siêu máy tính (ORD-2026-007)
        </button>
      </div>

      <!-- MESSAGES FEED -->
      <div id="messages-container" class="flex-1 overflow-y-auto p-5 space-y-4">
        <!-- Welcome Message -->
        <div class="flex gap-3 max-w-3xl">
          <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center shrink-0">
            <i class="fa-solid fa-robot text-sm"></i>
          </div>
          <div class="bg-slate-800/80 border border-slate-700/70 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 shadow-sm leading-relaxed">
            <div class="font-semibold text-white mb-1 flex items-center gap-2">
              <span>Trợ lý Kho vận ReAct</span>
              <span class="text-[10px] px-2 py-0.2 rounded bg-blue-500/20 text-blue-300 font-normal">AI Agent</span>
            </div>
            Xin chào! Tôi là Trợ lý Tác tử Kho vận kết nối MCP Server. Tôi có thể hỗ trợ bạn:
            <ul class="list-disc list-inside mt-2 space-y-1 text-slate-300 text-xs">
              <li>Tra cứu thông tin vận đơn, mặt hàng & vị trí kệ kho chính xác (Tool <code class="text-blue-400">query_shipment</code>).</li>
              <li>Cập nhật trạng thái và điều chuyển vị trí lưu kho thời gian thực (Tool <code class="text-emerald-400">update_order_status</code>).</li>
              <li>Giải đáp quy chuẩn lưu kho và vận hành chuỗi cung ứng.</li>
            </ul>
            <p class="text-xs text-slate-400 mt-2">👉 Hãy chọn một câu hỏi Test Case ở trên hoặc nhập yêu cầu trực tiếp bên dưới!</p>
          </div>
        </div>
      </div>

      <!-- INPUT BAR -->
      <div class="p-4 border-t border-slate-800 bg-slate-900/80">
        <form id="chat-form" onsubmit="sendMessage(event)" class="flex gap-2">
          <input
            id="user-input"
            type="text"
            placeholder="Nhập yêu cầu tra cứu đơn hàng hoặc cập nhật trạng thái kho..."
            class="flex-1 bg-slate-800/90 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            autocomplete="off"
          />
          <button
            id="send-btn"
            type="submit"
            class="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition shadow-lg shadow-blue-600/30 flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            <span>Gửi</span>
            <i class="fa-solid fa-paper-plane text-xs"></i>
          </button>
        </form>
      </div>
    </section>

    <!-- RIGHT COLUMN: REACT FLOW & LIVE OBSERVABILITY (40%) -->
    <aside class="w-5/12 flex flex-col bg-slate-950 overflow-hidden">
      
      <!-- FLOW HEADER -->
      <div class="px-5 py-3 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-2 text-xs font-bold text-slate-200">
          <i class="fa-solid fa-diagram-project text-blue-400"></i>
          <span>LUỒNG SUY LUẬN REACT & THỰC THI TOOL (LIVE TRACE)</span>
        </div>
        <span id="trace-badge" class="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
          Chờ truy vấn...
        </span>
      </div>

      <!-- TAB SELECTION: REACT STEPS VS LIVE INVENTORY -->
      <div class="flex border-b border-slate-800 bg-slate-900/30 text-xs">
        <button id="tab-trace" onclick="switchTab('trace')" class="flex-1 py-2 font-medium text-blue-400 border-b-2 border-blue-500 flex items-center justify-center gap-1.5 transition">
          <i class="fa-solid fa-timeline"></i> Các bước ReAct Loop
        </button>
        <button id="tab-inventory" onclick="switchTab('inventory')" class="flex-1 py-2 font-medium text-slate-400 hover:text-slate-200 border-b-2 border-transparent flex items-center justify-center gap-1.5 transition">
          <i class="fa-solid fa-warehouse"></i> CSDL Kho thời gian thực (<span id="inventory-badge-count" class="font-bold text-amber-400">10</span>)
        </button>
      </div>

      <!-- TRACE TIMELINE VIEW -->
      <div id="view-trace" class="flex-1 overflow-y-auto p-5 space-y-4">
        
        <div id="trace-empty" class="text-center py-16 text-slate-500 text-xs">
          <div class="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-600 text-xl">
            <i class="fa-solid fa-microchip"></i>
          </div>
          <p class="font-medium text-slate-400">Chưa có luồng thực thi nào</p>
          <p class="mt-1">Khi bạn gửi tin nhắn, chuỗi suy luận <span class="text-amber-400">Thought</span> ➔ <span class="text-blue-400">Action</span> ➔ <span class="text-emerald-400">Observation</span> sẽ hiển thị trực quan tại đây.</p>
        </div>

        <div id="trace-content" class="space-y-4 hidden">
          <!-- Dynamic Steps will be injected here -->
        </div>

      </div>

      <!-- INVENTORY VIEW -->
      <div id="view-inventory" class="flex-1 overflow-y-auto p-5 hidden space-y-3 text-xs">
        <div class="flex items-center justify-between text-slate-400 mb-1">
          <span class="font-semibold text-slate-200">Sơ đồ vị trí & Trạng thái Kiện hàng (WMS)</span>
          <button onclick="refreshInventory()" class="text-blue-400 hover:text-blue-300 flex items-center gap-1">
            <i class="fa-solid fa-rotate"></i> Cập nhật
          </button>
        </div>
        <div id="inventory-list" class="space-y-3">
          <!-- Dynamic inventory cards will be loaded here -->
        </div>
      </div>

      <!-- BOTTOM FOOTER -->
      <div class="p-3 border-t border-slate-800/80 bg-slate-900/50 text-[11px] text-slate-400 flex items-center justify-between shrink-0">
        <span class="flex items-center gap-1.5">
          <i class="fa-solid fa-circle-info text-blue-400"></i> Protocol: Model Context Protocol (JSON-RPC 2.0)
        </span>
        <span class="font-mono text-slate-500">File: docs/trace_waterfall.json</span>
      </div>

    </aside>

  </main>

  <script>
    const PROMPTS = {
      'TC01': 'Chào bạn, bạn có thể giới thiệu quy trình nhập kho và kiểm soát vị trí lưu kho tiêu chuẩn của chuỗi cung ứng không?',
      'TC02': 'Hãy tra cứu thông tin mã vận đơn và vị trí lưu kho của kiện hàng VN-LOG2026-01.',
      'TC03': 'Hãy cập nhật trạng thái đơn hàng VN-LOG2026-01 thành "Đã nhập kho" tại vị trí Kệ A-12, Tầng 3 vào lúc 14:30 hôm nay.',
      'TC04': 'Kiểm tra xem đơn hàng VN-LOG2026-01 hiện đang nằm ở vị trí kho nào, sau đó cập nhật trạng thái đơn hàng sang "Sẵn sàng xuất kho".',
      'TC05': 'Kiểm tra mã vận đơn VN-LOG9999-99 xem kiện hàng đang nằm ở vị trí kho nào và tình trạng ra sao?',
      'EX01': 'Hãy kiểm tra vị trí kho và số lượng tồn của kiện hàng Pin thể rắn VN-LOG2026-03.',
      'EX02': 'Tra cứu thông tin đơn hàng ORD-2026-007 xem máy chủ AI NVIDIA DGX H100 hiện lưu ở khu vực nào?'
    };

    async function setPrompt(tcKey) {
      const input = document.getElementById('user-input');
      input.value = PROMPTS[tcKey] || '';
      input.focus();
      // Khôi phục CSDL về trạng thái ban đầu ('Đã nhập kho') khi chọn TC02 hoặc TC04 để đảm bảo đúng kỳ vọng
      if (tcKey === 'TC02' || tcKey === 'TC04') {
        try {
          await fetch('/api/reset', { method: 'POST' });
          refreshInventory();
        } catch (e) {}
      }
    }

    function switchTab(tab) {
      const viewTrace = document.getElementById('view-trace');
      const viewInventory = document.getElementById('view-inventory');
      const tabTrace = document.getElementById('tab-trace');
      const tabInventory = document.getElementById('tab-inventory');

      if (tab === 'trace') {
        viewTrace.classList.remove('hidden');
        viewInventory.classList.add('hidden');
        tabTrace.className = 'flex-1 py-2 font-medium text-blue-400 border-b-2 border-blue-500 flex items-center justify-center gap-1.5 transition';
        tabInventory.className = 'flex-1 py-2 font-medium text-slate-400 hover:text-slate-200 border-b-2 border-transparent flex items-center justify-center gap-1.5 transition';
      } else {
        viewTrace.classList.add('hidden');
        viewInventory.classList.remove('hidden');
        tabTrace.className = 'flex-1 py-2 font-medium text-slate-400 hover:text-slate-200 border-b-2 border-transparent flex items-center justify-center gap-1.5 transition';
        tabInventory.className = 'flex-1 py-2 font-medium text-blue-400 border-b-2 border-blue-500 flex items-center justify-center gap-1.5 transition';
        refreshInventory();
      }
    }

    async function clearChat() {
      try {
        await fetch('/api/reset', { method: 'POST' });
        refreshInventory();
      } catch (e) {}
      const container = document.getElementById('messages-container');
      container.innerHTML = `
        <div class="flex gap-3 max-w-3xl">
          <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center shrink-0">
            <i class="fa-solid fa-robot text-sm"></i>
          </div>
          <div class="bg-slate-800/80 border border-slate-700/70 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 shadow-sm">
            Hộp thoại và CSDL kho vận đã được khôi phục về trạng thái ban đầu ('Đã nhập kho'). Bạn có thể chọn câu hỏi mới để thử nghiệm.
          </div>
        </div>
      `;
      document.getElementById('trace-empty').classList.remove('hidden');
      document.getElementById('trace-content').classList.add('hidden');
      document.getElementById('trace-badge').innerText = 'Chờ truy vấn...';
    }

    async function sendMessage(e) {
      e.preventDefault();
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      appendUserMessage(text);

      const sendBtn = document.getElementById('send-btn');
      sendBtn.disabled = true;
      sendBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang xử lý...';

      // Show thinking status in Trace view
      document.getElementById('trace-empty').classList.add('hidden');
      const traceContent = document.getElementById('trace-content');
      traceContent.classList.remove('hidden');
      traceContent.innerHTML = `
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-400 step-active">
          <i class="fa-solid fa-gear fa-spin text-blue-400 text-base mb-2"></i>
          <p class="font-medium text-slate-200">ReAct Loop đang kích hoạt...</p>
          <p class="text-[11px] text-slate-400 mt-0.5">Gọi LLM Provider ➔ Đánh giá Tool Calling Specs</p>
        </div>
      `;
      document.getElementById('trace-badge').innerText = 'Đang thực thi...';

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        appendAgentMessage(data.answer, data.traces, data);
        renderTraceWaterfall(data.traces);
        refreshInventory();

      } catch (err) {
        appendAgentMessage('Đã xảy ra lỗi khi kết nối tới Agent Server: ' + err.message, []);
      } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span>Gửi</span> <i class="fa-solid fa-paper-plane text-xs"></i>';
      }
    }

    function appendUserMessage(text) {
      const container = document.getElementById('messages-container');
      const msgDiv = document.createElement('div');
      msgDiv.className = 'flex justify-end';
      msgDiv.innerHTML = `
        <div class="max-w-2xl bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm shadow-md leading-relaxed">
          ${escapeHtml(text)}
        </div>
      `;
      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }

    function appendAgentMessage(answer, traces, meta = null) {
      const container = document.getElementById('messages-container');
      const msgDiv = document.createElement('div');
      msgDiv.className = 'flex gap-3 max-w-3xl';

      const hasToolCall = traces && traces.some(t => t.action_type === 'TOOL_EXECUTION');
      const toolBadge = hasToolCall
        ? '<span class="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold">🛠️ MCP Tool</span>'
        : '<span class="text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-300">Phản hồi trực tiếp</span>';

      let liveBadge = '';
      if (meta && meta.is_live_api) {
        liveBadge = `<span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1 font-mono">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          LIVE: ${meta.provider} (${meta.model}) • ${meta.total_duration_ms} ms
        </span>`;
      } else if (meta) {
        liveBadge = `<span class="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">Mock Offline</span>`;
      }

      msgDiv.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
          <i class="fa-solid fa-robot text-sm"></i>
        </div>
        <div class="bg-slate-800/90 border border-slate-700 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 shadow-md leading-relaxed">
          <div class="font-semibold text-white mb-2 flex items-center flex-wrap gap-2">
            <span>Trợ lý Kho vận ReAct</span>
            ${toolBadge}
            ${liveBadge}
          </div>
          <div class="whitespace-pre-wrap">${escapeHtml(answer)}</div>
        </div>
      `;
      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }

    function renderTraceWaterfall(traces) {
      const traceContent = document.getElementById('trace-content');
      if (!traces || traces.length === 0) {
        traceContent.innerHTML = '<p class="text-xs text-slate-400">Không có dữ liệu trace log.</p>';
        return;
      }

      document.getElementById('trace-badge').innerText = `${traces.length} Sự kiện Trace`;

      // Pipeline Header Bar
      let html = `
        <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 shadow-sm mb-4">
          <div class="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2 flex items-center justify-between">
            <span>Tiến trình ReAct Loop (4 Chặng chuẩn hóa):</span>
            <span class="text-emerald-400 font-mono">100% Hoàn tất</span>
          </div>
          <div class="grid grid-cols-4 gap-1.5 text-center text-[10px] font-semibold">
            <div class="py-1 px-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              1. 🧠 Thought
            </div>
            <div class="py-1 px-1 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
              2. 🛠️ Action
            </div>
            <div class="py-1 px-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              3. 👁️ Observation
            </div>
            <div class="py-1 px-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              4. 🏁 Final Answer
            </div>
          </div>
        </div>
      `;

      // Find tool execution step and final answer step
      const toolSteps = traces.filter(t => t.action_type === 'TOOL_EXECUTION');
      const finalStep = traces.find(t => t.action_type === 'FINAL_ANSWER') || traces[traces.length - 1];

      if (toolSteps.length > 0) {
        // Có gọi Tool (TC02, TC03, TC04, TC05)
        toolSteps.forEach((t, i) => {
          const stepNum = i + 1;
          html += `
            <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3 relative mb-4">
              <div class="flex items-center justify-between border-b border-slate-800 pb-2">
                <span class="text-xs font-bold text-white flex items-center gap-2">
                  <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px]">#${stepNum}</span>
                  CHU TRÌNH REACT (STEP ${stepNum})
                </span>
                <span class="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                  <i class="fa-regular fa-clock text-[10px] mr-1"></i>${t.latency_ms} ms
                </span>
              </div>

              <!-- BƯỚC 1: THOUGHT -->
              <div class="space-y-1">
                <div class="text-[11px] font-bold text-amber-400 flex items-center gap-1.5">
                  <span class="w-4 h-4 rounded-full bg-amber-500/20 flex items-center justify-center text-[9px]">1</span>
                  <span>🧠 BƯỚC 1: THOUGHT (TƯ DUY & LẬP LUẬN)</span>
                </div>
                <div class="p-3 rounded-lg bg-amber-950/20 border border-amber-800/40 text-xs text-amber-200 leading-relaxed font-sans">
                  ${escapeHtml(t.thought || 'LLM phân tích câu lệnh của người dùng, xác định mã định danh và quyết định gọi công cụ tương ứng.')}
                </div>
              </div>

              <!-- MŨI TÊN NỐI -->
              <div class="flex justify-center text-slate-600 text-xs py-0.5">
                <i class="fa-solid fa-arrow-down animate-bounce"></i>
              </div>

              <!-- BƯỚC 2: ACTION -->
              <div class="space-y-1">
                <div class="text-[11px] font-bold text-blue-400 flex items-center gap-1.5">
                  <span class="w-4 h-4 rounded-full bg-blue-500/20 flex items-center justify-center text-[9px]">2</span>
                  <span>🛠️ BƯỚC 2: ACTION (HÀNH ĐỘNG GỌI TOOL QUA MCP)</span>
                </div>
                <div class="p-3 rounded-lg bg-slate-950 border border-blue-800/50 font-mono text-xs space-y-1.5">
                  <div class="flex items-center justify-between text-blue-300 font-bold">
                    <span>Tool: <code class="text-amber-400 text-xs">${t.tool_name}</code></span>
                    <span class="text-[10px] text-slate-500 font-sans">JSON-RPC 2.0</span>
                  </div>
                  <div class="bg-slate-900 p-2 rounded text-[11px] text-slate-300 overflow-x-auto">
                    <pre>${JSON.stringify(t.arguments, null, 2)}</pre>
                  </div>
                </div>
              </div>

              <!-- MŨI TÊN NỐI -->
              <div class="flex justify-center text-slate-600 text-xs py-0.5">
                <i class="fa-solid fa-arrow-down animate-bounce"></i>
              </div>

              <!-- BƯỚC 3: OBSERVATION -->
              <div class="space-y-1">
                <div class="text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                  <span class="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center text-[9px]">3</span>
                  <span>👁️ BƯỚC 3: OBSERVATION (KẾT QUẢ TỪ MCP SERVER)</span>
                </div>
                <div class="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/40 font-mono text-[11px] text-emerald-200 overflow-x-auto max-h-48">
                  <pre>${JSON.stringify(t.observation, null, 2)}</pre>
                </div>
              </div>
            </div>
          `;
        });

        // BƯỚC 4: FINAL ANSWER
        if (finalStep) {
          html += `
            <div class="flex justify-center text-slate-600 text-xs py-0.5">
              <i class="fa-solid fa-arrow-down text-indigo-400 animate-bounce"></i>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/90 border border-indigo-800/60 shadow-lg space-y-2">
              <div class="text-[11px] font-bold text-indigo-400 flex items-center justify-between border-b border-slate-800 pb-2">
                <span class="flex items-center gap-1.5">
                  <span class="w-4 h-4 rounded-full bg-indigo-500/20 flex items-center justify-center text-[9px]">4</span>
                  <span>🏁 BƯỚC 4: FINAL ANSWER (TỔNG HỢP KẾT LUẬN)</span>
                </span>
                <span class="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">${finalStep.latency_ms} ms</span>
              </div>
              ${finalStep.thought ? `
                <div class="p-2.5 rounded-lg bg-amber-950/20 border border-amber-800/40 text-xs text-amber-200 leading-relaxed font-sans">
                  <div class="text-[10px] font-bold text-amber-400 mb-1 flex items-center gap-1">
                    <span>🧠 SUY LUẬN TỔNG HỢP:</span>
                  </div>
                  ${escapeHtml(finalStep.thought)}
                </div>
              ` : ''}
              <div class="p-3 rounded-lg bg-indigo-950/20 border border-indigo-800/40 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
                ${escapeHtml(finalStep.output)}
              </div>
            </div>
          `;
        }

      } else {
        // Phản hồi trực tiếp (Direct text - TC01)
        const t = finalStep;
        html += `
          <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <span class="text-xs font-bold text-white flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center text-[10px]">#1</span>
                TRUY VẤN TRỰC TIẾP (DIRECT REASONING)
              </span>
              <span class="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                ${t.latency_ms} ms
              </span>
            </div>

            <!-- BƯỚC 1: THOUGHT -->
            <div class="space-y-1">
              <div class="text-[11px] font-bold text-amber-400 flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full bg-amber-500/20 flex items-center justify-center text-[9px]">1</span>
                <span>🧠 BƯỚC 1: THOUGHT (TƯ DUY & LẬP LUẬN)</span>
              </div>
              <div class="p-3 rounded-lg bg-amber-950/20 border border-amber-800/40 text-xs text-amber-200 leading-relaxed">
                ${escapeHtml(t.thought || 'Yêu cầu là câu hỏi chung về quy chuẩn kho vận. LLM nhận thấy thông tin đã có sẵn trong System Prompt nên không cần gọi Tool qua MCP Server.')}
              </div>
            </div>

            <!-- MŨI TÊN NỐI -->
            <div class="flex justify-center text-slate-600 text-xs py-0.5">
              <i class="fa-solid fa-arrow-down"></i>
            </div>

            <!-- BƯỚC 2: ACTION -->
            <div class="space-y-1">
              <div class="text-[11px] font-bold text-blue-400 flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full bg-blue-500/20 flex items-center justify-center text-[9px]">2</span>
                <span>🛠️ BƯỚC 2: ACTION (QUYẾT ĐỊNH HÀNH ĐỘNG)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 font-mono flex items-center justify-between">
                <span>Trạng thái: <span class="text-blue-300 font-semibold">Bỏ qua gọi Tool (Direct Generation)</span></span>
                <span class="text-[10px] text-slate-500">Zero Tool Calls</span>
              </div>
            </div>

            <!-- MŨI TÊN NỐI -->
            <div class="flex justify-center text-slate-600 text-xs py-0.5">
              <i class="fa-solid fa-arrow-down"></i>
            </div>

            <!-- BƯỚC 3: OBSERVATION -->
            <div class="space-y-1">
              <div class="text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center text-[9px]">3</span>
                <span>👁️ BƯỚC 3: OBSERVATION (NGUỒN TRI THỨC)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/30 text-xs text-emerald-300">
                Sử dụng tri thức tham số nội tại và System Prompt của Trợ lý Kho vận.
              </div>
            </div>

            <!-- MŨI TÊN NỐI -->
            <div class="flex justify-center text-slate-600 text-xs py-0.5">
              <i class="fa-solid fa-arrow-down"></i>
            </div>

            <!-- BƯỚC 4: FINAL ANSWER -->
            <div class="space-y-1">
              <div class="text-[11px] font-bold text-indigo-400 flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full bg-indigo-500/20 flex items-center justify-center text-[9px]">4</span>
                <span>🏁 BƯỚC 4: FINAL ANSWER (CÂU TRẢ LỜI CHO NGƯỜI DÙNG)</span>
              </div>
              <div class="p-3 rounded-lg bg-indigo-950/20 border border-indigo-800/40 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                ${escapeHtml(t.output)}
              </div>
            </div>
          </div>
        `;
      }

      traceContent.innerHTML = html;
    }

    async function refreshInventory() {
      const container = document.getElementById('inventory-list');
      try {
        const res = await fetch('/api/inventory');
        const data = await res.json();
        
        const count = Object.keys(data).length;
        const countBadge = document.getElementById('inventory-badge-count');
        if (countBadge) countBadge.innerText = count;

        let html = '';
        for (const [key, item] of Object.entries(data)) {
          const isStored = item.status.includes('Đã nhập') || item.status.includes('Lưu kho');
          const statusColor = isStored ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30';
          
          html += `
            <div class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-2">
              <div class="flex items-center justify-between">
                <span class="font-mono font-bold text-blue-400 text-xs">${key}</span>
                <span class="text-[10px] px-2 py-0.5 rounded border ${statusColor}">
                  ${item.status}
                </span>
              </div>
              <div class="text-slate-200 font-medium">${item.item_name || 'Hàng hóa kho'}</div>
              <div class="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                <div><span class="text-slate-500">Vị trí:</span> <span class="text-amber-300 font-mono">${item.warehouse_location || 'N/A'}</span></div>
                <div><span class="text-slate-500">Số lượng:</span> <span class="text-white">${item.quantity || 1} kiện</span></div>
              </div>
              <div class="text-[10px] text-slate-500 flex justify-between">
                <span>Cập nhật: ${item.last_updated || 'Gần đây'}</span>
                <span>${item.recipient || ''}</span>
              </div>
            </div>
          `;
        }
        container.innerHTML = html;
      } catch (err) {
        container.innerHTML = '<p class="text-rose-400 text-xs">Không thể tải dữ liệu kho: ' + err.message + '</p>';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  </script>
</body>
</html>
"""


class AgentChatHandler(BaseHTTPRequestHandler):
    """Xử lý HTTP requests cho Chat Web App và API ReAct Agent"""

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif url.path == "/api/status":
            provider = get_llm_provider()
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_data = {
                "status": "ONLINE",
                "provider": provider.__class__.__name__,
                "model": getattr(provider, 'model_name', 'default'),
                "is_live_api": provider.__class__.__name__ != "MockOfflineProvider"
            }
            self.wfile.write(json.dumps(status_data, ensure_ascii=False).encode("utf-8"))
        elif url.path == "/api/inventory":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MOCK_DATABASE, ensure_ascii=False).encode("utf-8"))
        elif url.path in ["/pipeline_infographic.jpg", "/docs/pipeline_infographic.jpg"]:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_dir, "docs", "pipeline_infographic.jpg")
            if os.path.exists(img_path):
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(img_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/api/reset":
            reset_mock_database()
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "RESET_SUCCESS", "inventory": MOCK_DATABASE}, ensure_ascii=False).encode("utf-8"))
            return

        elif url.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(post_data)
                user_message = payload.get("message", "").strip()
            except Exception:
                user_message = ""

            if not user_message:
                self.send_response(400)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                return

            # Nếu câu hỏi là TC04 (kiểm tra rồi cập nhật sang xuất kho),
            # đảm bảo trạng thái khởi đầu của đơn hàng là 'Đã nhập kho'
            msg_lower = user_message.lower()
            if ("kiểm tra" in msg_lower or "ở đâu" in msg_lower or "vị trí" in msg_lower) and ("xuất kho" in msg_lower or "sẵn sàng" in msg_lower):
                if MOCK_DATABASE.get("VN-LOG2026-01", {}).get("status") != "Đã nhập kho":
                    reset_mock_database()

            provider = get_llm_provider()
            mcp_server = MCPSupplyChainServer()
            model_info = getattr(provider, 'model_name', 'default')
            
            print(f"\n==================================================")
            print(f"🌐 [WEB REQUEST NHẬN ĐƯỢC]: '{user_message}'")
            print(f"📡 Đang gọi LIVE API: {provider.__class__.__name__} (Model: {model_info})...")
            
            start_time = time.time()
            traces = run_react_agent(user_message, provider, mcp_server)
            total_duration_ms = round((time.time() - start_time) * 1000, 2)
            
            print(f"✅ Hoàn tất gọi LLM & ReAct Loop trong {total_duration_ms} ms!")
            print(f"==================================================\n")
            
            # Tìm câu trả lời cuối cùng
            final_answer = "Đã hoàn tất xử lý yêu cầu."
            for t in reversed(traces):
                if t.get("action_type") == "FINAL_ANSWER":
                    final_answer = t.get("output", "")
                    break

            # Lưu vết vào trace_waterfall.json
            save_waterfall_trace(traces)

            response_data = {
                "status": "SUCCESS",
                "provider": provider.__class__.__name__,
                "model": model_info,
                "is_live_api": provider.__class__.__name__ != "MockOfflineProvider",
                "total_duration_ms": total_duration_ms,
                "answer": final_answer,
                "traces": traces,
                "inventory": MOCK_DATABASE
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_server(port=7860):
    """Khởi động Web Chat Server"""
    for p in [port, 7861, 8000, 8080, 5000]:
        try:
            server_address = ("", p)
            httpd = HTTPServer(server_address, AgentChatHandler)
            print("==========================================================")
            print("🌐 TRỢ LÝ ĐƠN HÀNG & KHO VẬN (SUPPLY CHAIN AGENT) - WEB CHAT")
            print("==========================================================")
            print(f"✅ Web Chat & Trace Visualizer đang hoạt động tại:")
            print(f"👉 http://localhost:{p}")
            print(f"👉 http://127.0.0.1:{p}\n")
            print("💡 Mở trình duyệt và truy cập vào link trên để chat trực quan!")
            print("🛑 Nhấn Ctrl + C để dừng máy chủ.")
            print("==========================================================")
            httpd.serve_forever()
            break
        except OSError:
            continue


if __name__ == "__main__":
    start_server()

