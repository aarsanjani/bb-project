/**
 * Spark Campaign Ops & Risk Register Swarm Client Controller
 * Renders prioritized risk cards, BigQuery/GCS citations, 3x3 Impact-Likelihood Heatmap,
 * and handles interactive swarm queries and replay animation.
 */

class SparkCampaignOpsController {
    constructor() {
        this.swarmData = null;
        this.initEventListeners();
        this.loadSwarmData();
    }

    initEventListeners() {
        const replayBtn = document.getElementById("btnReplaySwarm");
        if (replayBtn) {
            replayBtn.addEventListener("click", () => this.replaySwarmExecution());
        }

        const runQueryBtn = document.getElementById("btnRunSparkQuery");
        const queryInput = document.getElementById("sparkChatInput");
        if (runQueryBtn && queryInput) {
            runQueryBtn.addEventListener("click", () => this.handleSparkQuery());
            queryInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") this.handleSparkQuery();
            });
        }

        const quickBtns = document.querySelectorAll(".quick-prompt-btn");
        quickBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                if (queryInput) {
                    queryInput.value = btn.innerText;
                    this.handleSparkQuery();
                }
            });
        });
    }

    async loadSwarmData() {
        try {
            const res = await fetch('/api/spark/swarm-data');
            const data = await res.json();
            this.swarmData = data;
            this.renderRiskRegister(data.risk_register);
            this.renderActivityFeed(data.activity_log);
        } catch (err) {
            console.error("Error loading Spark swarm data:", err);
        }
    }

    renderRiskRegister(risks) {
        const container = document.getElementById("riskCardsContainer");
        if (!container) return;

        container.innerHTML = "";
        risks.forEach(risk => {
            const card = document.createElement("div");
            card.className = "sp-risk-card";

            const sevClass = risk.severity.toLowerCase();

            let citationsHtml = risk.citations.map(c => `<span class="citation-pill">${this.escapeHtml(c)}</span>`).join("");
            citationsHtml += `<span class="citation-pill interv">${risk.interventions_count} interventions</span>`;

            card.innerHTML = `
                <div class="risk-score-badge ${sevClass}">
                    <span class="score-num">${risk.score.toFixed(1)}</span>
                    <span class="score-tag">${risk.severity}</span>
                </div>
                <div class="risk-content-block">
                    <div class="risk-title-line">
                        <span class="risk-id-label">${risk.risk_id}</span>
                        ${this.escapeHtml(risk.title)}
                    </div>
                    <div class="risk-desc-line">${this.escapeHtml(risk.description)}</div>
                    <div class="risk-citations-row">${citationsHtml}</div>
                </div>
                <div class="risk-expand-arrow">&rsaquo;</div>
            `;

            container.appendChild(card);
        });
    }

    renderActivityFeed(logs) {
        const list = document.getElementById("activityFeedList");
        if (!list) return;

        list.innerHTML = "";
        logs.forEach(item => {
            const el = document.createElement("div");
            el.className = "activity-item";
            el.innerHTML = `
                <span class="act-time">${item.time}</span>
                <span class="act-event">${this.escapeHtml(item.event)}</span>
            `;
            list.appendChild(el);
        });
    }

    async handleSparkQuery() {
        const input = document.getElementById("sparkChatInput");
        const query = input?.value.trim();
        if (!query) return;

        const runBtn = document.getElementById("btnRunSparkQuery");
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerText = "Querying BQ & GCS...";
        }

        try {
            const res = await fetch('/api/spark/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const data = await res.json();
            
            // Highlight relevant risks
            this.showToast(`✦ Spark Assistant: ${data.response}`);
            if (input) input.value = "";
        } catch (err) {
            console.error("Spark query error:", err);
        } finally {
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.innerText = "Run →";
            }
        }
    }

    replaySwarmExecution() {
        const replayBtn = document.getElementById("btnReplaySwarm");
        if (replayBtn) replayBtn.innerText = "↺ Replaying Swarm...";

        const list = document.getElementById("activityFeedList");
        const logs = this.swarmData ? this.swarmData.activity_log : [];
        if (!list || logs.length === 0) return;

        list.innerHTML = "";
        const reversed = [...logs].reverse();

        reversed.forEach((item, idx) => {
            setTimeout(() => {
                const el = document.createElement("div");
                el.className = "activity-item";
                el.innerHTML = `
                    <span class="act-time">${item.time}</span>
                    <span class="act-event">${this.escapeHtml(item.event)}</span>
                `;
                list.prepend(el);

                if (idx === reversed.length - 1) {
                    if (replayBtn) replayBtn.innerHTML = '<span class="sp-replay-icon">↺</span> Replay';
                }
            }, idx * 120);
        });
    }

    showToast(message) {
        alert(message);
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

document.addEventListener("DOMContentLoaded", () => {
    window.sparkApp = new SparkCampaignOpsController();
});
