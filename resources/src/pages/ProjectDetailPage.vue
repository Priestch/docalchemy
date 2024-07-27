<template>
  <div class="project-detail-page">
    <DocumentViewer v-if="options$" :options="options$"></DocumentViewer>
  </div>
</template>

<script setup lang="ts">
import {useRoute} from "vue-router";
import {onMounted, ref} from "vue";
import {getProjectFileUrl} from "../api.js";
import DocumentViewer from "../components/DocumentViewer.vue";

const options$ = ref();

const route = useRoute();

onMounted(() => {
  options$.value = {
    src: getProjectFileUrl(route.params.id),
    resourcePath: "static/document-viewer",
    disableCORSCheck: true,
  };
})
</script>

<style scoped>
.project-detail-page {
  height: 100%;
}
</style>