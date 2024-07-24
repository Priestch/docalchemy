<template>
  <Upload @upload-success="goProjectPage"></Upload>
</template>

<script setup>
import Upload from "../components/Upload.vue";
import {useRouter} from "vue-router";
const router = useRouter()

function goProjectPage() {
  router.push('/project');
}
</script>

<style scoped>

</style>