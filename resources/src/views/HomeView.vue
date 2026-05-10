<template>
  <el-container class="home-page">
    <el-header height="160px">
      <el-upload
          class="file-upload"
          drag
          action="/api/documents"
          multiple
      >
        <el-icon class="el-icon--upload">
          <upload-filled/>
        </el-icon>
        <div class="el-upload__text">
          Drop file here or <em>click to upload</em>
        </div>
      </el-upload>
    </el-header>
    <el-main>
      <el-empty v-if="!tableData$" description="Please upload PDF files."/>
      <el-table v-else :data="tableData$" stripe style="width: 100%">
        <el-table-column prop="name" label="Name" width="300"/>
        <el-table-column prop="mime_type" label="Type" width="120"/>
        <el-table-column prop="page_count" label="Pages" width="80"/>
        <el-table-column prop="created_at" label="Created At"/>
      </el-table>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import {ElUpload, ElIcon, ElContainer, ElHeader, ElMain, ElEmpty, ElTable, ElTableColumn} from 'element-plus'
import {UploadFilled} from "@element-plus/icons-vue"
import {http} from "../http";
import { ref } from "vue";

const tableData$ = ref([])

http.get('/documents').then(response => {
  tableData$.value = response.data.items || []
})

</script>

<style scoped lang="scss">
.home-page {
  width: 80%;
  margin: 0 auto;

  .el-header {
    padding-top: 40px;
  }

  :deep(.el-upload) {
    --el-upload-dragger-padding-horizontal: 20px;

    .el-upload-dragger {
      padding-top: 0;
    }
  }
}
</style>