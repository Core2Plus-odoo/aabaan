/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AabaanCeoDashboard extends Component {
    static template = "aabaan_ceo_dashboard.Dashboard";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, error: null });
        onWillStart(async () => {
            try {
                this.state.data = await this.orm.call("aabaan.ceo.dashboard", "get_data", []);
            } catch (error) {
                this.state.error = String((error && error.message) || error);
            }
        });
    }

    fmt(value) {
        const n = Math.round(value || 0);
        const abs = Math.abs(n);
        if (abs >= 1e6) return (n / 1e6).toFixed(2) + "M";
        if (abs >= 1e4) return Math.round(n / 1e3).toLocaleString() + "K";
        return n.toLocaleString();
    }

    money(value) {
        return ((this.state.data && this.state.data.currency) || "AED") + " " + this.fmt(value);
    }

    barWidth(items, item) {
        const max = Math.max(1, ...items.map((i) => i.gross || 0));
        return Math.max(2, Math.round((100 * (item.gross || 0)) / max));
    }

    barCount(items, item) {
        const max = Math.max(1, ...items.map((i) => i.count || 0));
        return Math.max(2, Math.round((100 * (item.count || 0)) / max));
    }

    monthHeight(items, item) {
        const max = Math.max(1, ...items.map((i) => i.gross || 0));
        return Math.max(item.gross ? 4 : 0, Math.round((100 * (item.gross || 0)) / max));
    }

    open(item) {
        if (!item || !item.model) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: item.label || "Details",
            res_model: item.model,
            domain: item.domain || [],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openOverdueAr() {
        const ar = this.state.data && this.state.data.ar;
        if (!ar) return;
        this.open({ model: ar.model, domain: ar.overdue_domain, label: "Overdue receivables" });
    }
}

registry.category("actions").add("aabaan_ceo_dashboard", AabaanCeoDashboard);
