import {AttachmentViewMoveLine} from "./attachment_view_move_line";

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {listView} from "@web/views/list/list_view";
import {ListRenderer, listRendererProps} from "@web/views/list/list_renderer";
import {ListController} from "@web/views/list/list_controller";
import {SIZES} from "@web/core/ui/ui_utils";
import {computed, proxy, t, useProps} from "@odoo/owl";
import {makeActiveField} from "@web/model/relational_model/utils";

export class AccountMoveLineListController extends ListController {
    static template = "l10n_ve_reports.MoveLineListView";
    static components = {
        ...ListController.components,
        AttachmentViewMoveLine,
    };
    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.ui = useService("ui");
        this.mailPopoutService = useService("mail.popout");
        this.attachmentPreviewState = proxy({
            displayAttachment:
                localStorage.getItem("account.move_line_pdf_previewer_hidden") !==
                "false",
            selectedRecord: false,
            thread: null,
        });
        this.thread = computed(() => this.attachmentPreviewState.thread);
        this.popout = proxy({active: false});

        this.openRecord = () => {};
    }

    get previewEnabled() {
        return (
            !this.env.searchModel.context.disable_preview &&
            (this.ui.size >= SIZES.XXL || this.mailPopoutService.externalWindow)
        );
    }

    get modelParams() {
        const params = super.modelParams;
        params.config.activeFields.move_attachment_ids = makeActiveField();
        params.config.activeFields.move_attachment_ids.related = {
            fields: {
                mimetype: {name: "mimetype", type: "char"},
            },
            activeFields: {
                mimetype: makeActiveField(),
            },
        };
        return params;
    }

    togglePreview() {
        this.attachmentPreviewState.displayAttachment =
            !this.attachmentPreviewState.displayAttachment;
        localStorage.setItem(
            "account.move_line_pdf_previewer_hidden",
            this.attachmentPreviewState.displayAttachment
        );
    }

    setPopout(value) {
        if (this.attachmentPreviewState.thread?.attachmentsInWebClientView.length) {
            this.popout.active = value;
        }
    }

    setSelectedRecord(accountMoveLineData) {
        this.attachmentPreviewState.selectedRecord = accountMoveLineData;
        this.setThread(this.attachmentPreviewState.selectedRecord);
    }

    async setThread(accountMoveLineData) {
        if (
            !accountMoveLineData ||
            !accountMoveLineData.data.move_attachment_ids.records.length
        ) {
            this.attachmentPreviewState.thread = null;
            return;
        }
        const thread = this.store["mail.thread"].insert({
            attachments: accountMoveLineData.data.move_attachment_ids.records.map(
                (attachment) => ({
                    id: attachment.resId,
                    mimetype: attachment.data.mimetype,
                })
            ),
            id: accountMoveLineData.data.move_id.id,
            model: accountMoveLineData.fields["move_id"].relation,
        });
        if (
            !thread.message_main_attachment_id &&
            thread.attachmentsInWebClientView.length > 0
        ) {
            thread.update({
                message_main_attachment_id: thread.attachmentsInWebClientView[0],
            });
        }
        this.attachmentPreviewState.thread = thread;
    }
}

export class AccountMoveLineListRenderer extends ListRenderer {
    props = useProps({
        ...listRendererProps,
        setSelectedRecord: t.function().optional(),
    });

    onCellClicked(record, column, ev) {
        this.props.setSelectedRecord(record);
        super.onCellClicked(record, column, ev);
    }

    findFocusFutureCell(cell, cellIsInGroupRow, direction) {
        const futureCell = super.findFocusFutureCell(cell, cellIsInGroupRow, direction);
        if (futureCell) {
            const dataPointId = futureCell.closest("tr").dataset.id;
            const record = this.props.list.records.filter(
                (x) => x.id === dataPointId
            )[0];
            this.props.setSelectedRecord(record);
        }
        return futureCell;
    }
}
export const AccountMoveLineListView = {
    ...listView,
    Renderer: AccountMoveLineListRenderer,
    Controller: AccountMoveLineListController,
};

registry.category("views").add("account_move_line_list_oca", AccountMoveLineListView);
