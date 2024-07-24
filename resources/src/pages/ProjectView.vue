<template>
  <div>
    Project Page
  </div>
</template>

<script setup>
import {getProjects} from "../api.js";

getProjects().then((response) => {
  console.log(response);
})
</script>

<style scoped>

</style>