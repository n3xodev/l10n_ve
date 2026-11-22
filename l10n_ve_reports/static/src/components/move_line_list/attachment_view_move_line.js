import {AttachmentView} from "@mail/core/common/attachment_view";
import {onMounted, t, useProps} from "@odoo/owl";
import {useBus} from "@web/core/utils/hooks";

export class AttachmentViewMoveLine extends AttachmentView {
    static components = {AttachmentView};

    openInPopout = useProps.static("openInPopout", t.boolean());
    setPopout = useProps.static("setPopout", t.function());

    setup() {
        super.setup();
        if (this.openInPopout) {
            onMounted(this.onClickPopout);
        }
        useBus(this.uiService.bus, "resize", () => this.setPopout(false));
    }
}
