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
                            <div class="ui-thumbnails-title font-weight-bold">{{ tour.name }}</div>
                            <div class="ui-thumbnails-text">{{ tour.description }}</div>
                            <!-- TODO (high) add tour.tags[] -->
                        </td>
                    </tr>
                </table>
            </div>
    </div>
</template>

<script>
import $ from "jquery"; //TODO (high) can remove? can we avoid using jquery?
import _l from "utils/localization";
import { getAppRoot } from "onload/loadConfig";
import { getGalaxyInstance } from "app"; //TODO (high) can remove?
import axios from "axios"; //TODO (high) should put the Axios request in `services.js`? Is the thinking there just to keep all our APIs standardized in terms of like: error logging, some basic error messaging, and unit testing?
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
    },
    created() {
        let url = `${getAppRoot()}api/tours`;
        axios
            .get(url)
            .then((response) => {
                this.tours = response.data;
            })
            .catch((e) => {
                this.error = this._errorMessage(e);
            });
    }, //TODO (moderate) add load() "spinner"
    methods: {
        filtered: function (items) {
            this.nWorkflows = items.length;
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
        match(tour) {
            const query = this.search.toLowerCase();
            return (
                !query ||
                (tour.name && tour.name.toLowerCase().includes(query)) ||
                (tour.description && tour.description.toLowerCase().includes(query))
            ); //TODO (high) add tour.tags[]
        },
        _errorMessage(e) {
            const message = e && e.response && e.response.data && e.response.data.err_msg;
            return message || "Request failed for an unknown reason.";
        },
    },
};
</script>

