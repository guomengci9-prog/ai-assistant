<template>
  <router-view :key="$route.fullPath" />
</template>

<script setup lang="ts">
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  font-family: "Helvetica Neue", Arial, sans-serif;
  background: #f5f6fa;
}
</style>
