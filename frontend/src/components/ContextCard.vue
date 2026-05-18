<script>
export default {
  data() {
    return {
      collapse: true
    }
  },
  props: {
    card: {
      type: Object,
      required: true
    }
  },
  emits: ['remove'],
  computed: {
    keywordsString: {
      get() {
        return Array.isArray(this.card.keywords) ? this.card.keywords.join(', ') : this.card.keywords;
      },
      set(value) {
        this.card.keywords = value.split(',');
      }
    }
  }
}
</script>

<template>
    <div class="context-card">
        <h3>{{ card.name }} <span class="card-type">({{ card.type }})</span></h3>
        <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
        <div v-if="!collapse">          
          <h4>Name</h4>
          <input type="text" v-model="card.name" maxlength="25" />

          <h4>Content</h4>
          <textarea v-model="card.content" />

          <div v-if="card.type === 'location'">
            <div>
            <label>Parent Location: </label>
            <input v-model="card.parent_location" maxlength="200" />
            <span title="Parent location can be a kingdom or some other region the location belongs in.">
              ⓘ
            </span>
            </div>
            <div>
            <label>Child Locations: </label>
            <input v-model="card.child_locations" maxlength="200" />
            <span title="Multiple child locations, such as villages in a kingdom, can be seperated using commas.">
              ⓘ
            </span>
            </div>
          </div>

          <div v-if="card.type === 'character'" class="checkbox-field">
            <label>Create Character Memories: </label>
            <input v-model="card.create_memories" type="checkbox" class="custom-checkbox" />
          </div>

          <h4>Keywords (comma-separated)</h4>
          <input type="text" v-model="card.keywords" maxlength="200" />

          <button class="btn btn-danger" @click="$emit('remove')">Delete Card</button>
        </div>
    </div>
</template>

<style>
.context-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card textarea {
  min-height: 120px;
}
.context-card h4 {
  margin: 3px 0 3px;
}
.context-card button {
  margin-bottom: 10px;
}
.context-card .btn-danger {
  background: #ff4d4d;
}
.card-type {
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
}
</style>