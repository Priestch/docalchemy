<template>
  <el-upload
    drag
    accept="pdf,PDF"
    action="/api/v1/projects"
    :before-upload="validateUpload"
    :show-file-list="false"
    :on-success="handleSuccess"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
      Drop file here or <em>click to upload</em>
    </div>
    <template #tip>
      <div class="el-upload__tip" :class="{error: $message.length > 0}">
        Only support pdf files with a size less than 10M
      </div>
    </template>
  </el-upload>
</template>

<script setup>
import { UploadFilled } from '@element-plus/icons-vue'
import {ref} from "vue";

const emit = defineEmits(['upload-success'])

const $message = ref('')

function handleSuccess() {
  emit('upload-success')
}

function validateUpload(file) {
  const isPDF = file.type === 'application/pdf'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isPDF) {
    $message.value = 'Only support pdf files';
  }

  if (!isLt10M) {
    $message.value = 'Only support pdf files with a size less than 10M';
  }

  return isPDF && isLt10M
}
</script>

<style>
.el-upload__tip.error {
  font-weight: bold;
  color: red;
}
</style>