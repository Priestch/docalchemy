<template>
  <div>
    <el-table :data="projects$" style="width: 100%" :border="true">
      <el-table-column label="Name">
        <template #default="scope">
          <el-button link @click="viewProject(scope.row.id)">{{ scope.row.name }}</el-button>
        </template>
      </el-table-column>
      <el-table-column label="Status">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 0" type="success">Queuing</el-tag>
          <el-tag v-if="scope.row.status === 10" type="success">Processing</el-tag>
          <el-tag v-if="scope.row.status === 100" type="success">Done</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {useRouter} from "vue-router";

const router = useRouter()
import {getProjects} from "../api.js";
import {onMounted, ref} from "vue";

const projects$ = ref();

onMounted(() => {
  getProjects().then((response) => {
    projects$.value = response.items;
  })
})

function viewProject(id) {
  router.push({name: 'projectDetail', params: { id }})
}
</script>

<style scoped>

</style>