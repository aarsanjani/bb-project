/**
 * ADK 2.x & A2UI Dynamic Client Component Factory & SSE Parser Engine
 * Handles real-time cognitive trace streaming, predictive agent node glowing,
 * and dynamic schema-driven component rendering for promotion pre-flight diagnostics.
 */

class MultiAgentDynamicUiEngine {
    constructor(streamApiUrl, chatTerminalId, canvasId) {
        this.streamApiUrl = streamApiUrl;
        this.chatTerminalId = chatTerminalId;
        this.canvasId = canvasId;
        this.activeEventSource = null;
        this.sessionId = "sim-session-live-" + Date.now().toString(36);
        
        this.initEventListeners();
        this.updateSessionDisplay();
    }

    updateSessionDisplay() {
        const sessionEl = document.getElementById("displaySessionId");
        if (sessionEl) {
            sessionEl.innerText = this.sessionId;
        }
    }

    initEventListeners() {
        const runBtn = document.getElementById("runSimulationBtn");
        if (runBtn) {
            runBtn.addEventListener("click", () => this.startSimulation());
        }

        const presetSelect = document.getElementById("promoPresetSelect");
        const promptInput = document.getElementById("customPromptInput");
        if (presetSelect && promptInput) {
            const defaultPrompts = {
                "promo-summer-tech": "Before I launch this promotion, show me exactly what will happen across every store, SKU, supplier and fulfillment channel and tell me the best intervention if something goes wrong.",
                "promo-flash-weekend": "Simulate 48-hour flash weekend sale with 40% storewide discounts, checking in-store POS queues, stockouts, and BOPIS thresholds.",
                "promo-apparel-home": "Simulate multi-week home essentials promo across store clusters, vendor lead times, and omnichannel shipping capacity."
            };
            promptInput.value = defaultPrompts[presetSelect.value] || "";
            presetSelect.addEventListener("change", (e) => {
                promptInput.value = defaultPrompts[e.target.value] || "";
            });
        }

        const toggleTermBtn = document.getElementById("toggleTerminalBtn");
        const termWrapper = document.getElementById("traceTerminalWrapper");
        if (toggleTermBtn && termWrapper) {
            toggleTermBtn.addEventListener("click", () => {
                termWrapper.classList.toggle("collapsed");
                toggleTermBtn.innerText = termWrapper.classList.contains("collapsed") ? "Expand Terminal" : "Collapse Terminal";
            });
        }

        const clearTermBtn = document.getElementById("clearTerminalBtn");
        const chatTerm = document.getElementById(this.chatTerminalId);
        if (clearTermBtn && chatTerm) {
            clearTermBtn.addEventListener("click", () => {
                chatTerm.innerHTML = '<div class="terminal-entry system-welcome"><span class="terminal-timestamp">[CLEARED]</span><span class="terminal-msg">Trace logs cleared.</span></div>';
            });
        }
    }

    startSimulation() {
        const promptInput = document.getElementById("customPromptInput");
        const userPrompt = promptInput.value.trim() || "Simulate complete promotion across Store, SKU, Supplier and Fulfillment channels";
        const runBtn = document.getElementById("runSimulationBtn");

        // Close existing stream if active
        if (this.activeEventSource) {
            this.activeEventSource.close();
            this.activeEventSource = null;
        }

        // Reset mesh node visuals
        this.resetMeshNodes();
        this.setLeadOrchestratorState("running");

        // Update mesh status badge
        const meshBadge = document.getElementById("meshStatusBadge");
        if (meshBadge) {
            meshBadge.innerText = "Simulating...";
            meshBadge.style.color = "var(--accent-blue)";
        }

        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerHTML = '<span class="status-pulse-dot"></span> Simulating Multi-Agent Mesh...';
        }

        // Add start entry to terminal
        this.appendTerminalLog("System", `Starting simulation session [${this.sessionId}] for intent: "${userPrompt}"`, "system");

        // Prepare query parameters including selected preset_id
        const presetSelect = document.getElementById("promoPresetSelect");
        const presetId = presetSelect ? presetSelect.value : "";
        const queryUrl = `${this.streamApiUrl}?prompt=${encodeURIComponent(userPrompt)}&session_id=${encodeURIComponent(this.sessionId)}&preset_id=${encodeURIComponent(presetId)}`;
        
        // Open EventSource SSE
        this.activeEventSource = new EventSource(queryUrl);

        this.activeEventSource.onmessage = (event) => {
            try {
                if (!event.data) return;
                const rpcFrame = JSON.parse(event.data);
                this.routeRpcFrame(rpcFrame);
            } catch (err) {
                console.error("Error parsing SSE JSON-RPC frame:", err, event.data);
            }
        };

        this.activeEventSource.onerror = (err) => {
            console.warn("EventSource pipeline closed / finished.", err);
            this.activeEventSource.close();
            this.activeEventSource = null;
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.innerHTML = '<span class="btn-icon">▶</span> Re-Run Multi-Agent Simulation';
            }
            if (meshBadge) {
                meshBadge.innerText = "Completed";
                meshBadge.style.color = "var(--accent-emerald)";
            }
            this.setLeadOrchestratorState("done");
        };
    }

    routeRpcFrame(frame) {
        const { method, params } = frame;
        if (!method) return;

        switch (method) {
            case "onAgentThought":
                this.appendTerminalLog(params.author, params.message, "thought");
                break;

            case "onAgentDelegation":
                this.handleAgentDelegation(params.author, params.target, params.message);
                break;

            case "onToolCall":
                this.appendTerminalLog(params.author, `Invoking Tool [${params.tool}] -> Args: ${JSON.stringify(params.arguments)}`, "tool");
                break;

            case "onUiComponentDelivery":
                this.buildDeclarativeWidgetFromSchema(params.payload, this.canvasId);
                break;

            case "onSimulationComplete":
                this.handleSimulationComplete(params);
                break;

            default:
                console.log("Unhandled method:", method, params);
        }
    }

    handleAgentDelegation(sourceAgent, targetAgent, message) {
        this.appendTerminalLog(sourceAgent, `Delegating control to [${targetAgent}]: ${message}`, "delegation");
        this.activateMeshNode(targetAgent);
    }

    handleSimulationComplete(params) {
        this.appendTerminalLog("LeadPromotionOrchestrator", `Simulation Completed. Status: ${params.status}. Executive Decision: ${params.executive_decision}.`, "done");
        this.showToast(`Simulation Complete: ${params.interventions_count} Interventions Synthesized!`);
        if (this.activeEventSource) {
            this.activeEventSource.close();
            this.activeEventSource = null;
        }
        const runBtn = document.getElementById("runSimulationBtn");
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<span class="btn-icon">▶</span> Re-Run Multi-Agent Simulation';
        }
    }

    appendTerminalLog(author, message, type) {
        const chatTerm = document.getElementById(this.chatTerminalId);
        if (!chatTerm) return;

        const entry = document.createElement("div");
        entry.className = "terminal-entry";

        let typeClass = "trace-type-thought";
        if (type === "tool") typeClass = "trace-type-tool";
        if (type === "delegation") typeClass = "trace-type-delegation";

        const timeStr = new Date().toLocaleTimeString();
        entry.innerHTML = `
            <span class="trace-author">[${author} - ${timeStr}]:</span>
            <span class="${typeClass}">${this.escapeHtml(message)}</span>
        `;

        chatTerm.appendChild(entry);
        chatTerm.scrollTop = chatTerm.scrollHeight;
    }

    /* Mesh Topology Visual State Management */
    resetMeshNodes() {
        const workerNodes = ["store_demand_agent", "sku_inventory_agent", "supplier_capacity_agent", "fulfillment_logistics_agent"];
        workerNodes.forEach(nodeId => {
            const el = document.getElementById(`node_${nodeId}`);
            const ind = document.getElementById(`status_${nodeId}`);
            if (el) el.className = "agent-node-card worker-node";
            if (ind) ind.className = "node-status-indicator";
        });
    }

    setLeadOrchestratorState(state) {
        const ind = document.getElementById("status_LeadPromotionOrchestrator");
        if (ind) {
            ind.className = `node-status-indicator ${state}`;
        }
    }

    activateMeshNode(targetAgent) {
        const el = document.getElementById(`node_${targetAgent}`);
        const ind = document.getElementById(`status_${targetAgent}`);
        if (el) {
            el.classList.add("active-delegated");
        }
        if (ind) {
            ind.className = "node-status-indicator running";
        }

        // Mark previously running nodes as done
        setTimeout(() => {
            if (ind && ind.classList.contains("running")) {
                ind.className = "node-status-indicator done";
                if (el) {
                    el.classList.remove("active-delegated");
                    el.classList.add("active-executing");
                }
            }
        }, 1200);
    }

    /* Dynamic Component Factory Pattern */
    buildDeclarativeWidgetFromSchema(schema, targetContainerId) {
        const container = document.getElementById(targetContainerId);
        if (!container) return;

        container.innerHTML = ""; // Clear canvas

        if (schema.type === "Dashboard") {
            // Dashboard Header
            const header = document.createElement("div");
            header.className = "a2ui-dashboard-header";
            header.innerHTML = `
                <h2 class="a2ui-dashboard-title">${this.escapeHtml(schema.title || "Simulation Dashboard")}</h2>
                <div class="a2ui-dashboard-subtitle">${this.escapeHtml(schema.subtitle || "")}</div>
            `;
            container.appendChild(header);

            // Render Child Components
            if (schema.components && Array.isArray(schema.components)) {
                schema.components.forEach(comp => {
                    this.renderComponent(comp, container);
                });
            }
        }
    }

    renderComponent(comp, parentEl) {
        switch (comp.type) {
            case "MetricGrid":
                this.renderMetricGrid(comp, parentEl);
                break;
            case "Tabs":
                this.renderTabs(comp, parentEl);
                break;
            case "Table":
                this.renderTable(comp, parentEl);
                break;
            case "AlertBanner":
                this.renderAlertBanner(comp, parentEl);
                break;
            case "Card":
                this.renderCard(comp, parentEl);
                break;
            case "InterventionList":
                this.renderInterventionList(comp, parentEl);
                break;
            default:
                console.warn("Unknown A2UI component type:", comp.type);
        }
    }

    renderMetricGrid(comp, parentEl) {
        const grid = document.createElement("div");
        grid.className = "a2ui-metric-grid";

        (comp.metrics || []).forEach(m => {
            const card = document.createElement("div");
            card.className = `a2ui-metric-card metric-status-${m.status || 'neutral'}`;
            card.innerHTML = `
                <div class="metric-label">${this.escapeHtml(m.label)}</div>
                <div class="metric-value">${this.escapeHtml(m.value)}</div>
                <div class="metric-subtext">${this.escapeHtml(m.subtext || m.trend || '')}</div>
            `;
            grid.appendChild(card);
        });

        parentEl.appendChild(grid);
    }

    renderTabs(comp, parentEl) {
        const wrapper = document.createElement("div");
        wrapper.className = "a2ui-tabs-wrapper";

        const nav = document.createElement("div");
        nav.className = "a2ui-tabs-nav";

        const panesWrapper = document.createElement("div");
        panesWrapper.className = "a2ui-tabs-panes";

        const tabItems = comp.components || [];

        tabItems.forEach((tab, idx) => {
            // Create Tab Button
            const btn = document.createElement("button");
            btn.className = `a2ui-tab-btn ${idx === 0 ? 'active' : ''}`;
            btn.innerText = tab.title;
            btn.dataset.tabId = tab.id || `tab_${idx}`;

            // Create Tab Pane
            const pane = document.createElement("div");
            pane.className = `a2ui-tab-pane ${idx === 0 ? 'active' : ''}`;
            pane.id = tab.id || `tab_${idx}`;

            // Render sub-components inside tab pane
            if (tab.components && Array.isArray(tab.components)) {
                tab.components.forEach(subComp => {
                    this.renderComponent(subComp, pane);
                });
            }

            // Click listener
            btn.addEventListener("click", () => {
                nav.querySelectorAll(".a2ui-tab-btn").forEach(b => b.classList.remove("active"));
                panesWrapper.querySelectorAll(".a2ui-tab-pane").forEach(p => p.classList.remove("active"));
                btn.classList.add("active");
                pane.classList.add("active");
            });

            nav.appendChild(btn);
            panesWrapper.appendChild(pane);
        });

        wrapper.appendChild(nav);
        wrapper.appendChild(panesWrapper);
        parentEl.appendChild(wrapper);
    }

    renderTable(comp, parentEl) {
        const container = document.createElement("div");
        container.className = "a2ui-table-container";

        if (comp.title) {
            const titleEl = document.createElement("div");
            titleEl.className = "a2ui-table-title";
            titleEl.innerText = comp.title;
            container.appendChild(titleEl);
        }

        const table = document.createElement("table");
        table.className = "a2ui-table";

        // Headers
        const thead = document.createElement("thead");
        const trHead = document.createElement("tr");
        (comp.headers || []).forEach(h => {
            const th = document.createElement("th");
            th.innerText = h;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement("tbody");
        (comp.rows || []).forEach(row => {
            const tr = document.createElement("tr");
            row.forEach((cell, cellIdx) => {
                const td = document.createElement("td");
                const cellText = String(cell);

                // Add badge styling if cell is a status code
                if (cellText.includes("CRITICAL") || cellText.includes("HIGH_RISK") || cellText.includes("OPTIMAL") || cellText.includes("CONSTRAINED") || cellText.includes("HEALTHY") || cellText.includes("RESPONSIVE") || cellText.includes("SECURE") || cellText.includes("STABLE") || cellText.includes("MODERATE")) {
                    const badge = document.createElement("span");
                    badge.className = `badge-status badge-${cellText.trim()}`;
                    badge.innerText = cellText;
                    td.appendChild(badge);
                } else {
                    td.innerText = cellText;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        container.appendChild(table);
        parentEl.appendChild(container);
    }

    renderAlertBanner(comp, parentEl) {
        const banner = document.createElement("div");
        banner.className = `a2ui-alert-banner ${comp.severity || 'warning'}`;
        banner.innerHTML = `
            <div class="alert-title">⚠ ${this.escapeHtml(comp.title || "System Alert")}</div>
            <div class="alert-message">${this.escapeHtml(comp.message || "")}</div>
        `;
        parentEl.appendChild(banner);
    }

    renderCard(comp, parentEl) {
        const card = document.createElement("div");
        card.className = "a2ui-card";

        const headerRow = document.createElement("div");
        headerRow.className = "card-header-row";
        headerRow.innerHTML = `
            <h3 class="card-title">${this.escapeHtml(comp.title || "")}</h3>
            ${comp.badge ? `<span class="card-badge">${this.escapeHtml(comp.badge)}</span>` : ''}
        `;
        card.appendChild(headerRow);

        const content = document.createElement("div");
        content.className = "card-content-text";
        content.innerHTML = this.formatMarkdown(comp.content || "");
        card.appendChild(content);

        parentEl.appendChild(card);
    }

    renderInterventionList(comp, parentEl) {
        const grid = document.createElement("div");
        grid.className = "interventions-grid";

        (comp.items || []).forEach(inv => {
            const card = document.createElement("div");
            card.className = "intervention-card";
            card.innerHTML = `
                <div class="intervention-header">
                    <div>
                        <div class="intervention-title">${this.escapeHtml(inv.title)}</div>
                        <div class="intervention-category">${this.escapeHtml(inv.category)}</div>
                    </div>
                    <span class="priority-pill">${this.escapeHtml(inv.priority)}</span>
                </div>
                <div class="intervention-body">
                    <div class="intervention-trigger"><strong>Trigger:</strong> ${this.escapeHtml(inv.trigger_condition)}</div>
                    <div class="intervention-desc">${this.escapeHtml(inv.action_description)}</div>
                    <div class="intervention-impact">✔ <strong>Mitigation:</strong> ${this.escapeHtml(inv.risk_mitigation)}</div>
                </div>
                <div class="intervention-footer">
                    <div class="intervention-metrics">
                        <span class="cost-tag">Cost: ${this.escapeHtml(inv.implementation_cost)}</span>
                        <span class="roi-tag">Expected ROI: ${this.escapeHtml(inv.net_roi)}</span>
                    </div>
                    <button class="btn-apply-intervention" data-intervention-id="${inv.intervention_id}">
                        ⚡ Apply Intervention
                    </button>
                </div>
            `;

            const applyBtn = card.querySelector(".btn-apply-intervention");
            if (applyBtn) {
                applyBtn.addEventListener("click", () => this.applyIntervention(inv.intervention_id, applyBtn));
            }

            grid.appendChild(card);
        });

        parentEl.appendChild(grid);
    }

    async applyIntervention(interventionId, btnElement) {
        btnElement.disabled = true;
        btnElement.innerText = "Applying...";

        try {
            const response = await fetch('/api/interventions/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ intervention_id: interventionId, action: 'EXECUTE' })
            });
            const data = await response.json();
            if (response.ok) {
                btnElement.classList.add("applied");
                btnElement.innerText = "✔ Applied (Active)";
                this.showToast(`Intervention Engaged: ${data.title}`);
                this.appendTerminalLog("InterventionEngine", `Engaged circuit breaker [${interventionId}]: ${data.message}`, "delegation");
            } else {
                btnElement.disabled = false;
                btnElement.innerText = "Retry";
                this.showToast(`Failed to apply intervention: ${data.error}`);
            }
        } catch (err) {
            console.error("Error applying intervention:", err);
            btnElement.disabled = false;
            btnElement.innerText = "Retry";
        }
    }

    showToast(message) {
        const container = document.getElementById("toastContainer");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = "toast";
        toast.innerHTML = `<span>⚡</span><span>${this.escapeHtml(message)}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 4000);
    }

    formatMarkdown(text) {
        if (!text) return "";
        let formatted = this.escapeHtml(text);
        formatted = formatted.replace(/### (.*?)\n/g, '<h3>$1</h3>');
        formatted = formatted.replace(/## (.*?)\n/g, '<h2>$1</h2>');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/- (.*?)\n/g, '<li>$1</li>');
        formatted = formatted.replace(/\n\n/g, '<br><br>');
        return formatted;
    }

    escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize Dynamic UI Engine on DOM Load
document.addEventListener("DOMContentLoaded", () => {
    window.uiEngine = new MultiAgentDynamicUiEngine("/api/chat/stream", "chatTerminal", "a2uiCanvas");
});
