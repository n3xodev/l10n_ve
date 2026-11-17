/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { NotificationPlugin } from "@web/core/notifications/notification_plugin";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ActionManagerPlugin } from "@web/webclient/actions/action_plugin";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

import { Component, onMounted, usePlugin, xml } from "@odoo/owl";

const USB_CHUNK = 16384;
const EPSON_USB_VENDOR_ID = 0x04b8;

function isUsbOpenAccessDeniedError(error) {
    if (!error) {
        return false;
    }
    const name = error.name || "";
    const msg = (error.message || "").toLowerCase();
    return (
        name === "SecurityError" ||
        name === "NetworkError" ||
        msg.includes("access denied") ||
        msg.includes("failed to execute 'open'") ||
        msg.includes("failed to open")
    );
}

async function sendEpsonEscpWebUSB(uint8Array) {
    if (!navigator.usb) {
        throw new Error(_t("WebUSB no está disponible (use Chrome/Edge y HTTPS)."));
    }
    const device = await navigator.usb.requestDevice({
        filters: [{ vendorId: EPSON_USB_VENDOR_ID }],
    });
    try {
        await device.open();
    } catch (e) {
        if (isUsbOpenAccessDeniedError(e)) {
            const err = new Error("USB_OPEN_ACCESS_DENIED");
            err.cause = e;
            throw err;
        }
        throw e;
    }
    try {
        const config =
            device.configuration ||
            device.configurations.find((c) => c.configurationValue === 1) ||
            device.configurations[0];
        if (!config) {
            throw new Error(_t("El dispositivo USB no tiene configuración."));
        }
        if (device.configuration === null) {
            await device.selectConfiguration(config.configurationValue);
        }
        const configuration = device.configuration;
        for (const iface of configuration.interfaces) {
            const alternate = iface.alternates[0];
            if (!alternate) {
                continue;
            }
            const bulkOut = alternate.endpoints.find(
                (e) => e.type === "bulk" && e.direction === "out"
            );
            if (!bulkOut) {
                continue;
            }
            try {
                await device.claimInterface(iface.interfaceNumber);
            } catch (e) {
                if (isUsbOpenAccessDeniedError(e)) {
                    const err = new Error("USB_CLAIM_ACCESS_DENIED");
                    err.cause = e;
                    throw err;
                }
                throw e;
            }
            try {
                for (let offset = 0; offset < uint8Array.length; offset += USB_CHUNK) {
                    const chunk = uint8Array.subarray(
                        offset,
                        Math.min(offset + USB_CHUNK, uint8Array.length)
                    );
                    await device.transferOut(bulkOut.endpointNumber, chunk);
                }
            } finally {
                await device.releaseInterface(iface.interfaceNumber);
            }
            return;
        }
        throw new Error(
            _t(
                "No se encontró un endpoint de salida compatible. Compruebe que sea una impresora Epson ESC/P por USB."
            )
        );
    } finally {
        try {
            await device.close();
        } catch {
            /* ignore */
        }
    }
}

export class L10nVeInvoiceEscpPrintAction extends Component {
    static target = "new";
    static props = { ...standardActionServiceProps };
    static template = xml`<div class="o_invisible_modifier"/>`;

    setup() {
        this.orm = useService("orm");
        this.notification = usePlugin(NotificationPlugin);
        this.action = usePlugin(ActionManagerPlugin);
        onMounted(() => this.run());
    }

    async run() {
        const moveId = this.props.action.params?.move_id;
        try {
            if (!moveId) {
                this.notification.add(_t("Falta el identificador de la factura."), {
                    type: "danger",
                });
                return;
            }
            const { payload_b64: b64 } = await this.orm.call(
                "account.move",
                "l10n_ve_invoice_escp_get_payload",
                [moveId]
            );
            const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
            await sendEpsonEscpWebUSB(bytes);
            await this.orm.call(
                "account.move",
                "l10n_ve_invoice_escp_confirm_printed",
                [moveId]
            );
            this.notification.add(_t("Impresión enviada a la impresora."), {
                type: "success",
            });
        } catch (e) {
            let msg = e?.message || String(e);
            if (e?.data?.message) {
                msg =
                    typeof e.data.message === "string"
                        ? e.data.message
                        : e.data.message?.toString?.() || msg;
            }
            if (
                e?.message === "USB_OPEN_ACCESS_DENIED" ||
                e?.message === "USB_CLAIM_ACCESS_DENIED"
            ) {
                msg = _t(
                    "Permiso USB denegado. Cierre otras pestañas que usen la impresora o conceda acceso en el navegador."
                );
            }
            this.notification.add(msg, { type: "danger" });
        } finally {
            try {
                await this.action.doAction({ type: "ir.actions.act_window_close" });
            } catch {
                /* dialog closed */
            }
        }
    }
}

registry.category("actions").add("l10n_ve_invoice_escp_print", L10nVeInvoiceEscpPrintAction);
