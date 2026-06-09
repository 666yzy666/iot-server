<template>
  <div class="app-root">
    <div ref="etherRef" class="ether-bg"></div>
    <router-view />
  </div>
</template>

<script setup>
import { useDotField } from './composables/useDotField.js'

const etherRef = useDotField({
  color: '168,85,247',   // primary purple
  density: 1.2,
  lineDistance: 150,
  repelStrength: 10
})
</script>

<style scoped>
.app-root {
  position: relative;
  min-height: 100vh;
}
.ether-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  width: 100%;
  height: 100%;
}
</style>
