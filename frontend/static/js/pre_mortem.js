/**
 * Promo Pre-Mortem: Supply-Chain Digital Twin Client Controller
 * Dynamically reacts to campaign levers & stress sliders, renders SVG time-series charts,
 * and executes AI greedy multi-round intervention solver.
 */

class PreMortemDigitalTwinController {
    constructor() {
        this.interventionsApplied = [];
        this.currentData = null;
        this.debounceTimer = null;

        this.initSliders();
        this.initTabs();
        this.initButtons();
        this.recalculate();
    }

    initSliders() {
        const sliders = [
            { id: "slider_horizon", labelId: "val_horizon", format: (v) => `${v} d` },
            { id: "slider_discount", labelId: "val_discount", format: (v) => `${parseFloat(v).toFixed(2)}x` },
            { id: "slider_media", labelId: "val_media", format: (v) => `${parseFloat(v).toFixed(2)}x` },
            { id: "slider_uncertainty", labelId: "val_uncertainty", format: (v) => `${v}%` },
            { id: "slider_seed", labelId: "val_seed", format: (v) => `${v}` },
            { id: "slider_supplier_slip", labelId: "val_supplier_slip", format: (v) => `${v} d` },
            { id: "slider_wh_capacity", labelId: "val_wh_capacity", format: (v) => `${v}%` },
            { id: "slider_channel_capacity", labelId: "val_channel_capacity", format: (v) => `${v}%` },
            { id: "slider_competitor_response", labelId: "val_competitor_response", format: (v) => `${v}%` },
            { id: "slider_greedy_rounds", labelId: "val_greedy_rounds", format: (v) => `${v}` },
        ];

        sliders.forEach(s => {
            const input = document.getElementById(s.id);
            const label = document.getElementById(s.labelId);
            if (input && label) {
                input.addEventListener("input", (e) => {
                    label.innerText = s.format(e.target.value);
                    this.debouncedRecalculate();
                });
            }
        });
    }

    initTabs() {
        const tabBtns = document.querySelectorAll(".pm-tab-btn");
        const tabPanes = document.querySelectorAll(".pm-tab-pane");

        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                tabBtns.forEach(b => b.classList.remove("active"));
                tabPanes.forEach(p => p.classList.remove("active"));

                btn.classList.add("active");
                const targetId = `pane_${btn.dataset.tab}`;
                const pane = document.getElementById(targetId);
                if (pane) pane.classList.add("active");
            });
        });
    }

    initButtons() {
        const btnFind = document.getElementById("btnFindInterventions");
        if (btnFind) {
            btnFind.addEventListener("click", () => this.optimizeInterventions());
        }

        const btnReset = document.getElementById("btnResetEverything");
        if (btnReset) {
            btnReset.addEventListener("click", () => this.resetControls());
        }
    }

    resetControls() {
        document.getElementById("slider_horizon").value = 23;
        document.getElementById("val_horizon").innerText = "23 d";

        document.getElementById("slider_discount").value = 0.60;
        document.getElementById("val_discount").innerText = "0.60x";

        document.getElementById("slider_media").value = 1.00;
        document.getElementById("val_media").innerText = "1.00x";

        document.getElementById("slider_uncertainty").value = 12;
        document.getElementById("val_uncertainty").innerText = "12%";

        document.getElementById("slider_seed").value = 7;
        document.getElementById("val_seed").innerText = "7";

        document.getElementById("slider_supplier_slip").value = 8;
        document.getElementById("val_supplier_slip").innerText = "8 d";

        document.getElementById("slider_wh_capacity").value = 70;
        document.getElementById("val_wh_capacity").innerText = "70%";

        document.getElementById("slider_channel_capacity").value = 100;
        document.getElementById("val_channel_capacity").innerText = "100%";

        document.getElementById("slider_competitor_response").value = 25;
        document.getElementById("val_competitor_response").innerText = "25%";

        this.interventionsApplied = [];
        this.recalculate();
    }

    getPayload() {
        return {
            horizon: parseInt(document.getElementById("slider_horizon")?.value || 23),
            discount_mult: parseFloat(document.getElementById("slider_discount")?.value || 0.60),
            media_mult: parseFloat(document.getElementById("slider_media")?.value || 1.00),
            demand_uncertainty: parseInt(document.getElementById("slider_uncertainty")?.value || 12),
            seed: parseInt(document.getElementById("slider_seed")?.value || 7),
            supplier_slip: parseInt(document.getElementById("slider_supplier_slip")?.value || 8),
            wh_capacity: parseInt(document.getElementById("slider_wh_capacity")?.value || 70),
            channel_capacity: parseInt(document.getElementById("slider_channel_capacity")?.value || 100),
            competitor_response: parseInt(document.getElementById("slider_competitor_response")?.value || 25),
            optimize_for: document.getElementById("select_optimize_for")?.value || "Balanced (margin + service)",
            greedy_rounds: parseInt(document.getElementById("slider_greedy_rounds")?.value || 4),
            interventions_applied: this.interventionsApplied
        };
    }

    debouncedRecalculate() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.recalculate(), 100);
    }

    async recalculate() {
        const payload = this.getPayload();
        try {
            const res = await fetch('/api/digital-twin/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            this.currentData = data;
            this.renderDashboard(data);
        } catch (err) {
            console.error("Simulation recalculation error:", err);
        }
    }

    async optimizeInterventions() {
        const btn = document.getElementById("btnFindInterventions");
        btn.innerText = "Solving Greedy Rounds...";
        btn.disabled = true;

        const payload = this.getPayload();
        try {
            const res = await fetch('/api/digital-twin/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            this.interventionsApplied = ["INTV-AIR-PO", "INTV-WH-THROTTLE", "INTV-STOCK-REALLOC"];
            this.currentData = data;
            this.renderDashboard(data);

            btn.innerText = "✔ Best Interventions Applied";
            btn.style.background = "var(--pm-green)";
            setTimeout(() => {
                btn.innerText = "Find best interventions";
                btn.style.background = "var(--pm-blue)";
                btn.disabled = false;
            }, 3000);
        } catch (err) {
            console.error("Optimization solver error:", err);
            btn.disabled = false;
            btn.innerText = "Find best interventions";
        }
    }

    renderDashboard(data) {
        // 1. Top KPIs
        const oc = data.campaign_outcome;
        document.getElementById("kpi_units_sold").innerText = oc.units_sold;
        document.getElementById("kpi_revenue").innerText = oc.revenue;
        document.getElementById("kpi_margin").innerText = oc.gross_margin;
        document.getElementById("kpi_service_level").innerText = oc.service_level;
        document.getElementById("kpi_unserved").innerText = oc.unserved_demand;
        document.getElementById("kpi_unserved_dollars").innerText = oc.unserved_demand_dollars;
        document.getElementById("kpi_spend").innerText = oc.promo_logistics_spend;
        document.getElementById("kpi_spend_subtext").innerText = oc.media_spend_subtext;

        // 2. Headline Risks
        document.getElementById("headlineSummaryText").innerText = data.headline_summary;
        const breachContainer = document.getElementById("breachListContainer");
        breachContainer.innerHTML = "";
        data.headline_risks.forEach(br => {
            const row = document.createElement("div");
            row.className = "pm-breach-row";
            row.innerHTML = `
                <span class="badge-breach">BREACH</span>
                <span><strong>${this.escapeHtml(br.title)}</strong></span>
                <span class="breach-details">(${this.escapeHtml(br.details)})</span>
            `;
            breachContainer.appendChild(row);
        });

        // 3. Render SVG Time Series Chart (Demand vs Fulfilled)
        this.renderSvgTimeSeries(data.daily_series);

        // 4. Lost Units Breakdown Bars
        const lb = data.loss_breakdown;
        const totalLost = (lb.out_of_stock + lb.channel_order_cap + lb.dc_throughput) || 1;

        const pOos = Math.min(100, Math.round((lb.out_of_stock / totalLost) * 100));
        const pChan = Math.min(100, Math.round((lb.channel_order_cap / totalLost) * 100));
        const pDc = Math.min(100, Math.round((lb.dc_throughput / totalLost) * 100));

        document.getElementById("bar_out_of_stock").style.width = `${pOos}%`;
        document.getElementById("count_out_of_stock").innerText = lb.out_of_stock.toLocaleString();

        document.getElementById("bar_channel_cap").style.width = `${pChan}%`;
        document.getElementById("count_channel_cap").innerText = lb.channel_order_cap.toLocaleString();

        document.getElementById("bar_dc_throughput").style.width = `${pDc}%`;
        document.getElementById("count_dc_throughput").innerText = lb.dc_throughput.toLocaleString();

        // 5. Per-SKU Outcome Table
        const tbody = document.getElementById("skuTableBody");
        tbody.innerHTML = "";
        data.sku_outcomes.forEach(sku => {
            const tr = document.createElement("tr");
            const fillIsRed = sku.fill_num < 90.0;
            tr.innerHTML = `
                <td><strong>${this.escapeHtml(sku.sku)}</strong></td>
                <td>${sku.disc}</td>
                <td>${sku.media}</td>
                <td>${sku.demand.toLocaleString()}</td>
                <td>${sku.sold.toLocaleString()}</td>
                <td class="${fillIsRed ? 'td-red' : ''}">${sku.fill}</td>
                <td>${sku.unserved.toLocaleString()}</td>
                <td>${sku.revenue}</td>
                <td>${sku.margin}</td>
                <td class="${sku.so_days !== '-' ? 'td-red' : ''}">${sku.so_days}</td>
            `;
            tbody.appendChild(tr);
        });

        // 6. Interventions Deck
        const deck = document.getElementById("interventionsDeck");
        if (deck) {
            deck.innerHTML = "";
            (data.interventions_available || []).forEach(inv => {
                const card = document.createElement("div");
                card.className = `pm-card ${inv.applied ? 'interv-applied' : ''}`;
                card.style.borderLeft = inv.applied ? '3px solid var(--pm-green)' : '3px solid var(--pm-blue)';
                card.style.marginBottom = '10px';
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="font-size: 13px; color: var(--pm-text-main);">${this.escapeHtml(inv.title)}</h4>
                        <span style="font-family: var(--pm-font-mono); font-size: 11px; color: ${inv.applied ? 'var(--pm-green)' : 'var(--pm-text-muted)'};">
                            ${inv.applied ? '✔ ACTIVE GUARDRAIL' : 'READY TO ENGAGE'}
                        </span>
                    </div>
                    <p style="font-size: 12px; color: var(--pm-text-sub); margin: 6px 0;"><strong>Benefit:</strong> ${this.escapeHtml(inv.benefit)}</p>
                    <p style="font-size: 11px; color: var(--pm-text-muted); font-family: var(--pm-font-mono);">Cost: ${this.escapeHtml(inv.cost)}</p>
                `;
                deck.appendChild(card);
            });
        }

        // 7. Raw JSON Telemetry
        const jsonEl = document.getElementById("rawJsonViewer");
        if (jsonEl) {
            jsonEl.innerText = JSON.stringify(data, null, 2);
        }
    }

    renderSvgTimeSeries(series) {
        const svg = document.getElementById("demandChartSvg");
        if (!svg || !series || series.length === 0) return;

        const width = 600;
        const height = 180;
        const padX = 20;
        const padY = 20;

        const maxVal = Math.max(...series.map(s => Math.max(s.demand, s.fulfilled))) * 1.15;
        const minVal = 0;

        const n = series.length;
        const stepX = (width - 2 * padX) / Math.max(1, n - 1);

        const getY = (val) => height - padY - ((val - minVal) / (maxVal - minVal)) * (height - 2 * padY);

        let demandPoints = [];
        let fulfilledPoints = [];

        series.forEach((s, idx) => {
            const x = padX + idx * stepX;
            demandPoints.push(`${x},${getY(s.demand)}`);
            fulfilledPoints.push(`${x},${getY(s.fulfilled)}`);
        });

        // Grid lines
        let gridLines = '';
        [0.25, 0.5, 0.75, 1.0].forEach(ratio => {
            const y = height - padY - ratio * (height - 2 * padY);
            const valLabel = Math.round(maxVal * ratio / 1000) + 'k';
            gridLines += `
                <line x1="${padX}" y1="${y}" x2="${width - padX}" y2="${y}" stroke="#1e2d42" stroke-dasharray="3,3" />
                <text x="${padX}" y="${y - 4}" fill="#64748b" font-family="JetBrains Mono" font-size="9">${valLabel}</text>
            `;
        });

        svg.innerHTML = `
            ${gridLines}
            <polyline fill="none" stroke="var(--pm-blue)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" points="${demandPoints.join(' ')}" />
            <polyline fill="none" stroke="var(--pm-green)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" points="${fulfilledPoints.join(' ')}" />
        `;
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
    window.preMortemTwin = new PreMortemDigitalTwinController();
});
