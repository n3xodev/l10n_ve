import { Component, onWillDestroy, proxy, signal, t, usePlugin, useProps } from "@odoo/owl";
import { NotificationPlugin } from "@web/core/notifications/notification_plugin";
import {DateTimeInput} from "@web/core/datetime/datetime_input";
import {AnnotationPopoverLine} from "@l10n_ve_reports/components/account_report/line_name/popover_line/annotation_popover_line";
import {removeTaxGroupingFromLineId} from "@l10n_ve_reports/js/util";

const {DateTime} = luxon;

export class AccountReportAnnotationsPopover extends Component {
    static template = "l10n_ve_reports.AccountReportAnnotationsPopover";
    props = useProps({
        controller: t.object(),
        lineName: t.object(),
        lineID: t.string(),
        close: t.function().optional(),
        isAddingAnnotation: t.boolean().optional(),
    });
    static components = {
        DateTimeInput,
        AnnotationPopoverLine,
    };

    setup() {
        this.notificationService = usePlugin(NotificationPlugin);

        this.newAnnotation = proxy({
            value: this.props.isAddingAnnotation ? this._getNewAnnotation() : {},
        });

        this.annotations = proxy(
            this.props.controller.visibleAnnotations[
                removeTaxGroupingFromLineId(this.props.lineID)
            ]
        );

        this.popoverTable = signal.ref();
        this.currentPromise = null;

        onWillDestroy(async () => {
            if (this.currentPromise) {
                await this.currentPromise;
            }
        });
    }

    get isAddingAnnotation() {
        return Object.keys(this.newAnnotation.value).length !== 0;
    }

    async refreshAnnotations() {
        this.currentPromise = null;
        await this.props.controller.refreshAnnotations();
        this.annotations =
            this.props.controller.visibleAnnotations[
                removeTaxGroupingFromLineId(this.props.lineID)
            ];
        if (this.isAddingAnnotation) {
            this.cleanNewAnnotation();
        }
    }

    _getNewAnnotation() {
        const date = this.props.controller.options.date.date_to;
        return {
            date: DateTime.fromISO(date),
            text: "",
            lineID: this.props.lineID,
        };
    }

    cleanNewAnnotation() {
        this.newAnnotation.value = {};
    }

    addAnnotation() {
        this.newAnnotation.value = this._getNewAnnotation();
    }

    formatAnnotation(annotation) {
        return {
            id: annotation.id,
            date: annotation.date ? DateTime.fromISO(annotation.date) : null,
            text: annotation.text,
            lineID: annotation.line_id,
        };
    }

    async saveNewAnnotation(newAnnotation) {
        if (newAnnotation.text) {
            this.currentPromise = this.env.services.orm.call(
                "account.report.annotation.oca",
                "create",
                [
                    {
                        report_id: this.props.controller.options.report_id,
                        line_id: newAnnotation.lineID,
                        text: newAnnotation.text,
                        date: newAnnotation.date
                            ? newAnnotation.date.toFormat("yyyy-LL-dd")
                            : null,
                        fiscal_position_id:
                            this.props.controller.options.fiscal_position,
                    },
                ],
                {
                    context: this.props.context,
                }
            );
            // We're using a .then() here to make sure that even if the component is destroyed
            // we'll call the function to finalize the logic.
            this.currentPromise.then(async () => {
                await this.refreshAnnotations();
                if (this.popoverTable()) {
                    this.popoverTable().scrollIntoView({
                        behavior: "smooth",
                        block: "end",
                    });
                }
            });
        }
    }

    async deleteAnnotation(annotationId) {
        this.currentPromise = this.env.services.orm.call(
            "account.report.annotation.oca",
            "unlink",
            [annotationId],
            {context: this.props.controller.context}
        );
        await this.currentPromise;
        await this.refreshAnnotations();
    }

    async editAnnotation(editedAnnotation, existingAnnotation) {
        this.currentPromise = this.env.services.orm.call(
            "account.report.annotation.oca",
            "write",
            [
                [existingAnnotation.id],
                {text: editedAnnotation.text, date: editedAnnotation.date},
            ],
            {
                context: this.props.controller.context,
            }
        );
        await this.currentPromise;
        await this.refreshAnnotations();
    }
}
