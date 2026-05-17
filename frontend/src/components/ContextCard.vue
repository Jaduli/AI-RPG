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
          <input type="text" v-model="card.name" />

          <h4>Content</h4>
          <textarea v-model="card.content" />

          <div v-if="card.type === 'item'">
            <label>Item Type: </label>
            <select v-model="card.item_type">
              <option value="perishable">Perishable</option>
              <option value="weapon">Weapon</option>
              <option value="apparel">Armor/apparel</option>
              <option value="other">Other</option>
            </select>
            <div>
            <label>Equipped: </label>
            <input v-model="card.equipped" type="checkbox" class="custom-checkbox" />
            <span title="Equipped items will be used in story context.">
              ⓘ
            </span>
            </div>
          </div>

          <div v-if="card.type === 'location'">
            <div>
            <label>Parent Location: </label>
            <input v-model="card.parent_location">
            <span title="Parent location can be a kingdom or some other region the location belongs in.">
              ⓘ
            </span>
            </div>
            <div>
            <label>Child Locations: </label>
            <input v-model="card.child_locations">
            <span title="Multiple child locations, such as villages in a kingdom, can be seperated using commas.">
              ⓘ
            </span>
            </div>
          </div>

          <div v-if="card.type === 'character'" class="checkbox-field">
            <label>Create Character Memories: </label>
            <input v-model="card.create_memories" type="checkbox" class="custom-checkbox" />
          </div>

          <div v-if="card.type !== 'item'">
            <h4>Keywords (comma-separated)</h4>
            <input type="text" v-model="card.keywords" />
          </div>

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