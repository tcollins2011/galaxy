<template>
    <div class="ui-thumbnails">
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <div v-else>
            <h2>Galaxy Tours</h2>
            <p>This page presents a list of interactive tours available on this Galaxy server.
            Select any tour to get started (and remember, you can click 'End Tour' at any time).</p>
            <!-- Temp Idea for a search bar similar to visualizations to find and select tags -->
             <DelayedInput
                class="mb-3"
                :query="search"
                :placeholder="titleSearchVisualizations"
                :delay="100"
                @change="onSearch" />
        </div>

        <!--  Old logic for generating a button for each tag -- not fully implemented yet-->
        <!-- <div class="row mb-3">
            <div class="col-12 btn-group" role="group" aria-label="Tag selector">
                <button class="btn btn-primary tag-selector-button" tag-selector-button="<%- tag.key %>"> </button> 
            </div>
        </div> -->

        <!-- Render a list of all the tours -->
        <div v-for="tour in tours" :key="tour.name">
                <table v-if="match(tour)">
                    <tr class="ui-thumbnails-item" @click="select(tour)">
                        <td>
                            <div class="ui-thumbnails-title font-weight-bold">{{ tour.html }}</div>
                            <div class="ui-thumbnails-text">{{ tour.description }}</div>
                            <!-- We migth want to add tags here -->
                        </td>
                    </tr>
                </table>
            </div>
    </div>
</template>

<script>
import $ from "jquery";
import _l from "utils/localization";
import { getAppRoot } from "onload/loadConfig";
import { getGalaxyInstance } from "app";
import DelayedInput from "components/Common/DelayedInput";

export default {
    components: {
        DelayedInput,
    },
    data() {
        return {
            tours: [],
            hdas: [],
            search: "",
            selected: null,
            name: null,
            error: null,
            fixed: false,
            titleSearchTours: _l("search tours"),
        };
    },
    computed: {
        showNotFound() {
            return this.nWorkflows === 0 && this.filter;
        },
        showNotAvailable() {
            return this.nWorkflows === 0 && !this.filter;
        },
        showMessage() {
            return !!this.message;
        },
    },
    created() {
        this.root = getAppRoot();
        this.services = new Services({ root: this.root });
        this.load();
    },
    methods: {
        load() {
            this.loading = true;
            this.filter = "";
            this.services
                .getWorkflows()
                .then((workflows) => {
                    this.workflows = workflows;
                    this.nWorkflows = workflows.length;
                    this.loading = false;
                })
                .catch((error) => {
                    this.error = error;
                });
        },
        filtered: function (items) {
            this.nWorkflows = items.length;
        },
        createWorkflow: function (workflow) {
            window.location = `${this.root}workflows/create`;
        },
        importWorkflow: function (workflow) {
            window.location = `${this.root}workflows/import`;
        },
        executeWorkflow: function (workflow) {
            window.location = `${this.root}workflows/run?id=${workflow.id}`;
        },
        bookmarkWorkflow: function (workflow, checked) {
            const id = workflow.id;
            const tags = workflow.tags;
            const data = {
                show_in_tool_panel: checked,
                tags: tags,
            };
            this.services
                .updateWorkflow(id, data)
                .then(({ id, name }) => {
                    if (checked) {
                        getGalaxyInstance().config.stored_workflow_menu_entries.push({ id: id, name: name });
                    } else {
                        const indexToRemove = getGalaxyInstance().config.stored_workflow_menu_entries.findIndex(
                            (workflow) => workflow.id === id
                        );
                        getGalaxyInstance().config.stored_workflow_menu_entries.splice(indexToRemove, 1);
                    }

                    this.workflows.find((workflow) => {
                        if (workflow.id === id) {
                            workflow.show_in_tool_panel = checked;
                            return true;
                        }
                    });
                })
                .catch((error) => {
                    this.onError(error);
                });
        },
        onTags: function (tags, index) {
            const workflow = this.workflows[index];
            workflow.tags = tags;
            this.services
                .updateWorkflow(workflow.id, {
                    show_in_tool_panel: workflow.show_in_tool_panel,
                    tags: workflow.tags,
                })
                .catch((error) => {
                    this.onError(error);
                });
        },
        onAdd: function (workflow) {
            this.workflows.unshift(workflow);
            this.nWorkflows = this.workflows.length;
        },
        onRemove: function (id) {
            this.workflows = this.workflows.filter((item) => item.id !== id);
            this.nWorkflows = this.workflows.length;
        },
        onUpdate: function (id, data) {
            const workflow = this.workflows.find((item) => item.id === id);
            Object.assign(workflow, data);
            this.workflows = [...this.workflows];
        },
        onSuccess: function (message) {
            this.message = message;
            this.messageVariant = "success";
        },
        onError: function (message) {
            this.message = message;
            this.messageVariant = "danger";
        },
    },
};
</script>

