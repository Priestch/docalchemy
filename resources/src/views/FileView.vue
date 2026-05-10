<template>
  <DocumentViewer></DocumentViewer>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from 'vue-router';
import DocumentViewer from "../components/DocumentViewer.vue";

const route = useRoute()

const options$ = ref();

onMounted(() => {
  options$.value = {
    src: `/api/files/${route.params.id}/upload`,
    resourcePath: "/static/document-viewer",
    disableCORSCheck: true,
  };
})


</script>

<style scoped>

</style>