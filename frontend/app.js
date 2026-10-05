document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatArea = document.getElementById('chat-area');
    const welcomeCard = document.getElementById('welcome-card');
    const sendBtn = document.getElementById('send-btn');
    const currentUserId = "mgr123";

    // View panels
    const viewAgent = document.getElementById('view-agent');
    const viewSources = document.getElementById('view-sources');
    const viewArch = document.getElementById('view-arch');
    const navAgent = document.getElementById('nav-agent');
    const navSources = document.getElementById('nav-sources');
    const navArch = document.getElementById('nav-arch');

    marked.setOptions({ breaks: true, gfm: true });

    // ── Sidebar Navigation ──
    navAgent.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('agent');
    });
    navSources.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('sources');
    });
    navArch.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('arch');
    });

    function switchView(view) {
        // Remove active from all
        [viewAgent, viewSources, viewArch].forEach(v => v.classList.remove('active'));
        [navAgent, navSources, navArch].forEach(n => n.classList.remove('active'));

        if (view === 'agent') {
            viewAgent.classList.add('active');
            navAgent.classList.add('active');
        } else if (view === 'sources') {
            viewSources.classList.add('active');
            navSources.classList.add('active');
            loadSourcesData();
        } else {
            viewArch.classList.add('active');
            navArch.classList.add('active');
        }
    }

    // ── Load dynamic source data ──
    async function loadSourcesData() {
        try {
            const response = await fetch('/api/sources');
            if (response.ok) {
                const data = await response.json();
                const ragDocCount = document.getElementById('rag-doc-count');
                if (ragDocCount) {
                    ragDocCount.textContent = `${data.total_indexed} indexed`;
                }
            }
        } catch (err) {
            console.log('Could not load sources data:', err);
        }
    }

    // ── Quick Action Buttons ──
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            queryInput.value = btn.dataset.query;
            chatForm.dispatchEvent(new Event('submit'));
        });
    });

    // ── Form Submit ──
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // Hide welcome card
        if (welcomeCard) welcomeCard.style.display = 'none';

        // Append user message
        appendUserMessage(query);
        queryInput.value = '';
        sendBtn.disabled = true;

        // Create agent response container
        const agentBlock = createAgentBlock();
        chatMessages.appendChild(agentBlock.container);
        scrollToBottom();

        try {
            const response = await fetch('/api/query_project_health', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, user_id: currentUserId })
            });

            if (!response.ok) throw new Error(`Server responded with ${response.status}`);
            const data = await response.json();

            // Store query for HTML export
            agentBlock._query = query;

            // Animate the REAL agent trace steps
            await animateRealTrace(agentBlock, data.agent_trace);

            // Render the final report
            renderAgentReport(agentBlock, data);

        } catch (error) {
            console.error('Error:', error);
            agentBlock.loading.remove();
            const errDiv = document.createElement('div');
            errDiv.className = 'agent-report';
            errDiv.innerHTML = `<p style="color: var(--accent-red);">⚠️ <strong>Error:</strong> ${error.message}</p>`;
            agentBlock.container.appendChild(errDiv);
        } finally {
            sendBtn.disabled = false;
            queryInput.focus();
        }
    });

    // ── Create User Message ──
    function appendUserMessage(text) {
        const block = document.createElement('div');
        block.className = 'msg-block msg-user';
        block.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
        chatMessages.appendChild(block);
        scrollToBottom();
    }

    // ── Create Agent Block ──
    function createAgentBlock() {
        const container = document.createElement('div');
        container.className = 'msg-block msg-agent';

        const tracePanel = document.createElement('div');
        tracePanel.className = 'agent-trace';

        const traceHeader = document.createElement('div');
        traceHeader.className = 'trace-header';
        traceHeader.innerHTML = `
            <div class="trace-title">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m16.07-7.07l-4.24 4.24m-1.66 1.66l-4.24 4.24m0-9.9l4.24 4.24m1.66 1.66l4.24 4.24"></path></svg>
                Agent Execution Trace
            </div>
            <svg class="trace-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
        `;

        const traceSteps = document.createElement('div');
        traceSteps.className = 'trace-steps';

        const loading = document.createElement('div');
        loading.className = 'step-loading';
        loading.innerHTML = `<span class="loading-text">Initializing agent pipeline...</span>`;
        traceSteps.appendChild(loading);

        tracePanel.appendChild(traceHeader);
        tracePanel.appendChild(traceSteps);
        container.appendChild(tracePanel);

        traceHeader.addEventListener('click', () => {
            traceHeader.classList.toggle('collapsed');
            traceSteps.classList.toggle('collapsed');
        });

        return { container, tracePanel, traceSteps, loading, _query: '' };
    }

    // ── Animate Real Trace Steps ──
    async function animateRealTrace(agentBlock, traceSteps) {
        const { traceSteps: stepsContainer, loading } = agentBlock;

        for (let i = 0; i < traceSteps.length; i++) {
            const step = traceSteps[i];
            loading.querySelector('.loading-text').textContent = step.action + '...';
            await sleep(350 + Math.random() * 250);
            const stepEl = createStepElement(step);
            stepsContainer.insertBefore(stepEl, loading);
            scrollToBottom();
        }

        loading.remove();
    }

    // ── Create Step Element ──
    function createStepElement(step) {
        const el = document.createElement('div');
        el.className = `trace-step status-${step.status}`;
        const elapsedMs = step.elapsed_ms ? ` · ${step.elapsed_ms}ms` : '';
        el.innerHTML = `
            <div class="step-content">
                <div class="step-agent">${escapeHtml(step.agent)}</div>
                <div class="step-action">${escapeHtml(step.action)}</div>
                <span class="step-tool">${escapeHtml(step.tool)}${elapsedMs}</span>
                ${step.details ? `<div class="step-details">${escapeHtml(step.details)}</div>` : ''}
            </div>
        `;
        return el;
    }

    // ── Render Final Report ──
    function renderAgentReport(agentBlock, data) {
        const reportDiv = document.createElement('div');
        reportDiv.className = 'agent-report';

        if (data.risk_score !== undefined && data.risk_status) {
            const riskClass = data.risk_status.toLowerCase().replace(' ', '-');
            reportDiv.innerHTML += `<div class="risk-badge ${riskClass}">${data.risk_status} — Risk Score: ${data.risk_score}/100</div>`;
        }

        reportDiv.innerHTML += marked.parse(data.report);

        // Source chips
        if (data.sources_used && data.sources_used.length > 0) {
            const sourceMap = {
                'SharePoint': 'sp',
                'Azure DevOps (MCP)': 'devops',
                'D365 Project Operations': 'd365',
                'ChromaDB + BM25 (Hybrid RAG)': 'rag'
            };
            let chipsHtml = '<div class="source-chips">';
            data.sources_used.forEach(src => {
                const dotClass = sourceMap[src] || 'sp';
                chipsHtml += `<div class="source-chip"><span class="dot ${dotClass}"></span>${src}</div>`;
            });
            chipsHtml += '</div>';
            reportDiv.innerHTML += chipsHtml;
        }

        // HTML Export button
        const exportBtn = document.createElement('button');
        exportBtn.className = 'export-btn';
        exportBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Export HTML Report
        `;
        exportBtn.addEventListener('click', async () => {
            exportBtn.disabled = true;
            exportBtn.textContent = 'Generating...';
            try {
                const resp = await fetch('/api/export_html', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: agentBlock._query, user_id: currentUserId })
                });
                if (resp.ok) {
                    const html = await resp.text();
                    const blob = new Blob([html], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'project_health_report.html';
                    a.click();
                    URL.revokeObjectURL(url);
                }
            } catch (err) {
                console.error('Export failed:', err);
            } finally {
                exportBtn.disabled = false;
                exportBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Export HTML Report
                `;
            }
        });
        reportDiv.appendChild(exportBtn);

        agentBlock.container.appendChild(reportDiv);
        scrollToBottom();
    }

    // ── Utilities ──
    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});
