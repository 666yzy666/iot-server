<template>
  <div class="stat">
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script setup>
defineProps({
  value: { type: [String, Number], default: "-" },
  label: { type: String, required: true },
});
</script>

<style scoped>
.stat {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 18px;
}
.stat-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  margin-top: 8px;
  color: var(--muted);
  font-size: 13px;
}
</style>
