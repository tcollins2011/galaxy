<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";
import Heading from "./Common/Heading.vue";
import LoadingSpan from "./LoadingSpan.vue";
import { useMarkdown } from "@/composables/markdown";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faThumbsUp, faThumbsDown } from "@fortawesome/free-solid-svg-icons";
import { library } from "@fortawesome/fontawesome-svg-core";

library.add(faThumbsUp, faThumbsDown);

const props = defineProps({
    view: {
        type: String,
        default: "wizard",
    },
    query: {
        type: String,
        default: "",
    },
    context: {
        type: String,
        default: "",
    },
});
const query = ref(props.query);
const queryResponse = ref("");
const busy = ref(false);
const feedback = ref<null | "up" | "down">(null);

const { renderMarkdown } = useMarkdown({ openLinksInNewPage: true, removeNewlinesAfterList: true });
// on submit, query the server and put response in display box
function submitQuery() {
    busy.value = true;
    queryResponse.value = "";
    const context = props.context || "username";
    axios
        .post("/api/chat", {
            query: query.value,
            context: context,
        })
        .then(function (response) {
            console.log(response);
            queryResponse.value = response.data;
        })
        .catch(function (error) {
            console.error(error);
        })
        .finally(() => {
            busy.value = false;
        });
}
</script>
<template>
    <div>
        <!-- input text, full width top of page -->
        <Heading v-if="props.view == 'wizard'" inline h2>Ask the wizard</Heading>
        <div :class="props.view == 'wizard' && 'mt-2'">
            <b-input
                v-if="props.query == ''"
                id="wizardinput"
                v-model="query"
                style="width: 100%"
                placeholder="What's the difference in fasta and fastq files?"
                @keyup.enter="submitQuery" />
            <b-button
                v-else-if="!queryResponse"
                variant="info"
                :disabled="busy"
                @click="submitQuery">
                <span v-if="!busy">
                    Let our Help Wizard Figure it out!
                </span>
                <LoadingSpan v-else message="Thinking..." />
            </b-button>
        </div>
        <!-- spinner when busy -->
        <div :class="props.view == 'wizard' && 'mt-4'">
            <div v-if="busy">
                <b-skeleton animation="wave" width="85%"></b-skeleton>
                <b-skeleton animation="wave" width="55%"></b-skeleton>
                <b-skeleton animation="wave" width="70%"></b-skeleton>
            </div>
            <div v-else class="chatResponse" v-html="renderMarkdown(queryResponse)" />

            <div v-if="queryResponse && !feedback" class="feedback-buttons mt-2">
                <h4>Was this answer helpful?</h4>
                <b-button variant="success" :disabled="feedback !== null">
                    <FontAwesomeIcon :icon="faThumbsUp" class="mr-1" />
                </b-button>
                <b-button variant="danger" :disabled="feedback !== null">
                    <FontAwesomeIcon :icon="faThumbsDown" class="mr-1" />
                </b-button>
            </div>
        </div>
    </div>
</template>
<style lang="scss" scoped>
.chatResponse {
    white-space: pre-wrap;
}
</style>