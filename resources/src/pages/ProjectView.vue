<template>
  <div>
    <el-table :data="projects$" style="width: 100%">
      <el-table-column prop="name" label="Name" />
      <el-table-column prop="status" label="Status"/>
    </el-table>
  </div>
</template>

<script setup>
import {getProjects} from "../api.js";
import {ref} from "vue";

const projects$ = ref();

getProjects().then((response) => {
  console.log("response", response);
  projects$.value = response.items;
})
</script>

<style scoped>

</style>