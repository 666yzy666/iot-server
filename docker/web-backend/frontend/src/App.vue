<template>
  <div class="app-root">
    <div ref="etherRef" class="ether-bg"></div>
    <router-view />
  </div>
</template>

<script setup>
import { useLiquidEther } from './composables/useLiquidEther.js'

const etherRef = useLiquidEther({
  colors: ['#2a1f3d', '#3d2a55', '#5a3f78']
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
