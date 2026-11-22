import { Component, proxy, signal, t, usePlugin, useProps } from "@odoo/owl";
import { NotificationPlugin } from "@web/core/notifications/notification_plugin";
import { useAutofocus } from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import {DateTimeInput} from "@web/core/datetime/datetime_input";
import { useLayoutEffect } from "@web/owl2/utils";

const {DateTime} = luxon;

export class AnnotationPopoverLine extends Component {
    static template = "l10n_ve_reports.AnnotationPopoverLine";
    props = useProps({
        annotation: t.object({
            date: t.or([t.instanceOf(DateTime), t.literal(false), t.literal(null)]).optional(),
            text: t.string(),
            lineID: t.string(),
            id: t.number().optional(),
        }),
        onEdit: t.function(),
        onDelete: t.function(),
    });
    static components = {
        DateTimeInput,
    };

    setup() {
        this.applyAutoresizeToAll(".annotation_popover_autoresize_textarea");
        this.annotation = proxy(this.props.annotation);
        this.notificationService = usePlugin(NotificationPlugin);
        this.textArea = signal.ref();
        if (!this.annotation.text.length) {
            useAutofocus({ref: this.textArea});
        }
    }

    applyAutoresizeToAll(selector) {
        useLayoutEffect(() => {
            const resizeTextArea = (textarea) => {
                textarea.style.height = `${textarea.scrollHeight}px`;
                textarea.parentElement.style.height = `${textarea.scrollHeight}px`;
            };

            const textareas = document.querySelectorAll(selector);
            for (const textarea of textareas) {
                Object.assign(textarea.style, {
                    width: "auto",
                    paddingTop: 0,
                    paddingBottom: 0,
                });
                resizeTextArea(textarea);
                textarea.addEventListener("input", () => {
                    resizeTextArea(textarea);
                });
            }
        });
    }

    annotationEditDate(date) {
        this.annotation.date = date;
        this.props.onEdit(this.annotation);
    }

    annotationEditText() {
        if (this.textArea().value) {
            if (this.textArea().value !== this.annotation.text) {
                this.annotation.text = this.textArea().value;
                this.props.onEdit(this.annotation);
            }
        } else {
            this.notificationService.add(
                _t("The annotation shouldn't have an empty value.")
            );
        }
    }

    deleteAnnotation() {
        this.props.onDelete(this.annotation.id);
    }
}
