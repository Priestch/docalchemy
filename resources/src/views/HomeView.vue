<template>
  <el-container class="home-page">
    <el-header height="160px">
      <el-upload
        class="file-upload"
        drag
        action="/api/files"
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
      <el-empty description="Please upload PDF files." />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ElUpload, ElIcon, ElContainer, ElHeader, ElMain, ElEmpty } from 'element-plus'
import {UploadFilled} from "@element-plus/icons-vue"

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