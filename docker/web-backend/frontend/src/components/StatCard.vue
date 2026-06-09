<template>
  <div class="stat-card">
    <div class="stat-inner">
      <div class="stat-value" :class="color">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  value: { type: [String, Number], default: '-' },
  label: { type: String, required: true },
  color: { type: String, default: 'primary' },
})
</script>

<style scoped>
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  position: relative;
  overflow: hidden;
  transition: all var(--transition);
  cursor: default;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0;
  transition: opacity var(--transition);
}
.stat-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: var(--glow); }
.stat-card:hover::before { opacity: 1; }
.stat-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1.2;
}
.stat-value.primary { color: var(--primary); }
.stat-value.success { color: var(--success); }
.stat-value.muted { color: var(--text-muted); }
.stat-value.warning { color: var(--warning); }
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
