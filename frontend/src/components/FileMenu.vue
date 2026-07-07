<script>
export default {
  props: {
    is_loading: Boolean
  },
  data() {
    return {
      files: [],
      show: true,
      error: ''
    }
  },
  methods: {
    async fetchFiles() {
      const parent = this.$parent;
      this.error = '';
      parent.active_requests++;
      try {
        const res = await fetch('/api/get_save_files');
        const data = await res.json();
        if (data.error) {
          throw new Error(data.error);
        }
        this.files = data.files || [];
      } catch (err) {
        this.error = 'Failed to load saved stories: ' + (err.message || err);
      } finally {
        parent.active_requests--;
      }
    },
    load(story_id) {
      this.$emit('load-file', story_id);
    }
  },
  mounted() {
    this.fetchFiles();
  }
}
</script>

<template>
  <div class="file-menu container">
    <div class="header-row">
      <h2>Saved Stories</h2>
      <button @click="show = !show">
        {{ show ? 'Collapse' : 'Expand' }}
      </button>
    </div>
    <div v-if="show">
      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="files.length === 0" class="info-message">No saved stories found.</div>

      <ul v-else class="file-list">
        <li v-for="file in files" :key="file.story_id">
          <span class="file-label">
            {{ file.story_id }} — {{ file.story_name || 'Untitled Story' }}
          </span>
          <button @click="load(file.story_id)" :disabled="is_loading">Load</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.file-menu {
  margin-bottom: 16px;
}
.file-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0 0;
}
.file-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  margin-bottom: 8px;
  background: #0f0f1e;
  border: 1px solid #24243e;
  border-radius: 4px;
}
.file-list li.selected {
  border-color: #aa3bff;
  background: rgba(170, 59, 255, 0.1);
}
.file-label {
  flex: 1;
  margin-right: 12px;
  color: #fff;
  font-size: 0.95rem;
}
.error-message,
.info-message {
  margin: 10px 0;
  color: #f4f4f4;
}
.error-message {
  color: #ff7f7f;
}
</style>
