import { mount } from "@vue/test-utils";
import flushPromises from "flush-promises";
import { getLocalVue } from "jest/helpers";
import SelectorModal from "./SelectorModal";

const localVue = getLocalVue();

const SELECTED_HISTORY_ID = "COOL_ID";
const getFakeHistorySummaries = (num, selectedIndex = 0) => {
    const result = Array.from({ length: num }, (_, index) => ({
        id: `ID-${index}`,
        name: `History-${index}`,
        tags: [],
        update_time: new Date().toISOString(),
    }));
    result[selectedIndex].id = SELECTED_HISTORY_ID;
    return result;
};
const PROPS_WITH_10_HISTORIES = {
    currentHistoryId: SELECTED_HISTORY_ID,
    histories: getFakeHistorySummaries(10),
    perPage: 3,
    static: true, // Force the modal visible for testing
};
const PROPS_WITH_10_HISTORY_MULTIPLE_SELECT = {
    ...PROPS_WITH_10_HISTORIES,
    multiple: true,
};

describe("History SelectorModal.vue", () => {
    let wrapper;

    async function mountWith(props) {
        wrapper = mount(SelectorModal, {
            propsData: props,
            localVue,
        });
        await flushPromises();
    }

    it("should highlight the currently selected history", async () => {
        await mountWith(PROPS_WITH_10_HISTORIES);

        const selectedRows = wrapper.findAll(".table-info");
        expect(selectedRows.length).toBe(1);
        expect(selectedRows.at(0).attributes("data-pk")).toBe(SELECTED_HISTORY_ID);
    });

    it("paginates the histories", async () => {
        await mountWith(PROPS_WITH_10_HISTORIES);

        const displayedRows = wrapper.findAll("tbody > tr").wrappers;
        expect(displayedRows.length).toBe(3);
        expect(wrapper.vm.histories.length).toBe(10);
    });

    it("emits selectHistory with the correct history ID when a row is clicked", async () => {
        await mountWith(PROPS_WITH_10_HISTORIES);

        expect(wrapper.emitted()["selectHistory"]).toBeUndefined();

        const targetHistoryId = "ID-2";
        const targetRow = wrapper.find(`[data-pk="${targetHistoryId}"]`);
        await targetRow.trigger("click");

        expect(wrapper.emitted()["selectHistory"]).toBeDefined();
        expect(wrapper.emitted()["selectHistory"][0][0].id).toBe(targetHistoryId);
    });

    it("select multiple histories", async () => {
        await mountWith(PROPS_WITH_10_HISTORY_MULTIPLE_SELECT);

        expect(wrapper.emitted()["selectHistories"]).toBeUndefined();

        const targetHistoryId1 = "ID-1";
        const targetRow1 = wrapper.find(`[data-pk="${targetHistoryId1}"]`);
        await targetRow1.trigger("click");

        const targetHistoryId2 = "ID-2";
        const targetRow2 = wrapper.find(`[data-pk="${targetHistoryId2}"]`);
        await targetRow2.trigger("click");

        expect(wrapper.vm.selectedHistories.length).toBe(2);

        const button = wrapper.find(".btn-primary");

        await button.trigger("click");

        expect(wrapper.emitted()["selectHistories"][0][0][0].id).toBe(targetHistoryId1);
    });
});
