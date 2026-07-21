const BASE = "/dhl_packstation_static";
const STATUS = {
  high: { color: "#67e86f", glow: "rgba(103,232,111,.42)", label: "Viele freie Fächer", badge: "GUTE KAPAZITÄT", image: `${BASE}/images/packstation_green.webp` },
  low: { color: "#ffc107", glow: "rgba(255,193,7,.42)", label: "Wenige freie Fächer", badge: "GERINGE KAPAZITÄT", image: `${BASE}/images/packstation_yellow.webp` },
  "very-low": { color: "#ff4d55", glow: "rgba(255,77,85,.45)", label: "Fast voll", badge: "SEHR GERINGE KAPAZITÄT", image: `${BASE}/images/packstation_red.webp` },
  unknown: { color: "#9aa4af", glow: "rgba(154,164,175,.28)", label: "Keine Prognose", badge: "STATUS UNBEKANNT", image: `${BASE}/images/packstation_yellow.webp` },
};
const DAYS = { Monday: "Mo", Tuesday: "Di", Wednesday: "Mi", Thursday: "Do", Friday: "Fr", Saturday: "Sa", Sunday: "So" };
const ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

class DHLPackstationCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("entity required");
    this.config = { view: "full", show_map: true, show_status_text: true, ...config };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return this.config?.view === "row" ? 1 : this.config?.view === "compact" ? 4 : 8;
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) => hass.states[id].attributes?.data_type === "average_capacity_by_weekday"
    );
    return { entity: entity || "", view: "full" };
  }

  _entity() { return this._hass?.states?.[this.config?.entity]; }
  _statusValue() {
    const entity = this._entity();
    return entity?.attributes?.capacity_today || entity?.state || "unknown";
  }
  _status() { return STATUS[this._statusValue()] || STATUS.unknown; }
  _title() {
    const entity = this._entity();
    return this.config?.name || entity?.attributes?.display_name || entity?.attributes?.friendly_name || "DHL Packstation";
  }
  _address() {
    const attrs = this._entity()?.attributes || {};
    return [attrs.street, attrs.postal_code, attrs.city].filter(Boolean).join(", ");
  }
  _weekly() {
    const attrs = this._entity()?.attributes || {};
    if (attrs.weekly_forecast) {
      return ORDER.map((dayOfWeek) => ({
        dayOfWeek,
        capacity: attrs.weekly_forecast[dayOfWeek] || "unknown",
      }));
    }
    const source = attrs.averageCapacityDayOfWeek || [];
    return ORDER.map((dayOfWeek) => source.find((item) => item.dayOfWeek === dayOfWeek) || { dayOfWeek, capacity: "unknown" });
  }
  _mapUrl() {
    const attrs = this._entity()?.attributes || {};
    if (attrs.latitude && attrs.longitude) {
      return `https://www.openstreetmap.org/?mlat=${attrs.latitude}&mlon=${attrs.longitude}#map=18/${attrs.latitude}/${attrs.longitude}`;
    }
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(this._address())}`;
  }

  render() {
    if (!this.config || !this._hass) return;
    const card = document.createElement("ha-card");
    const view = this.config.view || "full";
    card.className = view;
    card.innerHTML = this.css() + (view === "row" ? this.row() : view === "compact" ? this.compact() : this.full());
    card.addEventListener("click", () => {
      const event = new Event("hass-more-info", { bubbles: true, composed: true });
      event.detail = { entityId: this.config.entity };
      this.dispatchEvent(event);
    });
    this.replaceChildren(card);
  }

  full() {
    const status = this._status();
    const week = this._weekly().map((item) => {
      const dayStatus = STATUS[item.capacity] || STATUS.unknown;
      return `<div class="weekday"><span>${DAYS[item.dayOfWeek]}</span><i style="--dot:${dayStatus.color}"></i></div>`;
    }).join("");
    const map = this.config.show_map === false ? "" : `<a class="map" href="${this._mapUrl()}" target="_blank" rel="noopener" onclick="event.stopPropagation()"><ha-icon icon="mdi:map-marker-outline"></ha-icon></a>`;
    return `<div class="background" style="--bg:url('${status.image}');--status:${status.color};--glow:${status.glow}">
      <header><div class="square"><ha-icon icon="mdi:package-variant-closed"></ha-icon></div><div class="heading"><h1>${this._title()}</h1><p>${this._address()}</p></div>${map}</header>
      <section class="status"><div class="badge"><i></i><ha-icon icon="mdi:signal-cellular-3"></ha-icon><span>${status.badge}</span></div><div class="main-status">${status.label}</div></section>
      <section class="forecast"><div class="forecast-head"><strong>Wochenprognose</strong><ha-icon icon="mdi:chart-timeline-variant"></ha-icon></div><div class="week">${week}</div><div class="note"><ha-icon icon="mdi:information-outline"></ha-icon><span>DHL-Prognose anhand vergangener Wochen, kein aktueller Live-Füllstand</span></div></section>
    </div>`;
  }

  compact() {
    const status = this._status();
    return `<div class="compact-background" style="--bg:url('${status.image}');--status:${status.color};--glow:${status.glow}"><h2>${this._title()}</h2><div class="compact-label">${status.label}</div></div>`;
  }

  row() {
    const status = this._status();
    return `<div class="row-content" style="--status:${status.color};--glow:${status.glow}"><ha-icon icon="mdi:package-variant-closed"></ha-icon><strong>${this._title()}</strong><span class="grow"></span><i></i>${this.config.show_status_text === false ? "" : `<em>${status.label}</em>`}</div>`;
  }

  css() {
    return `<style>
      :host{display:block}ha-card{overflow:hidden;background:#05090d;color:#f4f7fa;border-radius:28px}.full{aspect-ratio:1/1}
      .background,.compact-background{position:relative;width:100%;height:100%;box-sizing:border-box;background-image:linear-gradient(90deg,rgba(3,8,13,.98),rgba(3,8,13,.92) 25%,rgba(3,8,13,.56) 46%,rgba(3,8,13,.04) 78%),linear-gradient(0deg,rgba(3,8,13,.94),transparent 60%),var(--bg);background-size:cover;background-position:58% center;background-repeat:no-repeat}
      .background{padding:5%}header{display:grid;grid-template-columns:56px minmax(0,1fr) 46px;gap:14px;align-items:center}.square,.map{display:flex;align-items:center;justify-content:center;border-radius:17px;background:rgba(5,11,17,.78);border:1px solid rgba(255,255,255,.11);color:#fff;text-decoration:none}.square{width:56px;height:56px}.map{width:46px;height:46px}.heading{min-width:0}.heading h1{margin:0;font-size:clamp(18px,2.7vw,34px);line-height:1.05;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.heading p{margin:7px 0 0;color:#9aa4b0;font-size:clamp(11px,1.25vw,16px);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .status{position:absolute;top:29%;left:5%;width:37%;max-width:360px}.badge{display:inline-flex;align-items:center;gap:8px;max-width:100%;box-sizing:border-box;padding:9px 14px;border-radius:999px;color:var(--status);border:1px solid var(--status);background:rgba(4,10,15,.84);box-shadow:0 0 22px var(--glow);font-weight:800;font-size:clamp(8px,.95vw,13px);letter-spacing:.035em}.badge span{white-space:normal}.badge i,.row-content i{width:10px;height:10px;flex:0 0 10px;border-radius:50%;background:var(--status);box-shadow:0 0 13px var(--status)}.main-status{margin-top:20px;color:var(--status);font-size:clamp(24px,3.3vw,43px);font-weight:820;line-height:.97;letter-spacing:-.04em;text-shadow:0 0 24px var(--glow);max-width:100%}
      .forecast{position:absolute;left:5%;right:5%;bottom:4.5%;padding:17px 16px 15px;border-radius:17px;background:rgba(4,10,15,.89);border:1px solid rgba(255,255,255,.09);backdrop-filter:blur(12px)}.forecast-head{display:flex;justify-content:space-between;align-items:center}.forecast-head ha-icon{color:var(--status)}.week{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;margin-top:11px}.weekday{display:flex;flex-direction:column;align-items:center;gap:6px;padding:7px 2px;border-radius:9px;background:rgba(255,255,255,.035);color:#aeb6c0}.weekday i{width:8px;height:8px;border-radius:50%;background:var(--dot);box-shadow:0 0 10px var(--dot)}.note{display:flex;justify-content:center;align-items:center;gap:6px;margin-top:12px;color:#818c98;font-size:clamp(8px,.85vw,11px)}
      .compact{aspect-ratio:4/3}.compact-background{padding:7%;display:flex;flex-direction:column;justify-content:space-between;background-image:linear-gradient(0deg,rgba(3,8,13,.9),transparent 65%),var(--bg);background-position:center}.compact-background h2{margin:0;font-size:clamp(20px,2.2vw,32px)}.compact-label{align-self:flex-start;color:var(--status);padding:9px 14px;border:1px solid var(--status);border-radius:999px;background:rgba(4,10,15,.82);box-shadow:0 0 18px var(--glow);font-weight:750}
      .row{border-radius:16px}.row-content{min-height:58px;padding:0 16px;display:flex;align-items:center;gap:12px}.row-content strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.grow{flex:1}.row-content em{color:var(--status);font-style:normal;font-weight:700;white-space:nowrap}
      @media(max-width:600px){.background{padding:4.5%}header{grid-template-columns:46px minmax(0,1fr) 40px;gap:9px}.square{width:46px;height:46px}.map{width:40px;height:40px}.status{top:28%;left:4.5%;width:42%}.badge{padding:7px 9px;font-size:8px}.main-status{margin-top:15px;font-size:clamp(21px,6.2vw,34px)}.forecast{left:4.5%;right:4.5%;bottom:4%;padding:12px 10px}.week{gap:3px}.weekday{padding:5px 1px}.note{display:none}.row-content em{display:none}}
    </style>`;
  }
}

customElements.define("dhl-packstation-card", DHLPackstationCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "dhl-packstation-card", name: "DHL Packstation Card", description: "DHL capacity forecast", preview: true });
