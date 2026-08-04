<script>
export default {
  data() {
    return {
      collapse: true,
      show_memories: false,
      new_memory: ''
    }
  },
  props: {
    card: {
      type: Object,
      required: true
    }
  },
  emits: ['remove'],
  methods: {
    removeMemory(index) {
      this.card.memories.splice(index, 1);
    },
    removeRelationshipMemory(relationship, index) {
      const relationships = this.card.relationship_memories;

      if (!relationships) {
        return;
      }

      if (Array.isArray(relationships)) {
        const relationship_index = relationship.sourceIndex;
        const relationship_entry = relationships[relationship_index];

        if (!Array.isArray(relationship_entry)) {
          return;
        }

        relationship_entry.splice(index, 1);

        if (relationship_entry.length === 0) {
          relationships.splice(relationship_index, 1);
        }
        return;
      }

      if (relationship.sourceKey && Array.isArray(relationships[relationship.sourceKey])) {
        relationships[relationship.sourceKey].splice(index, 1);

        if (relationships[relationship.sourceKey].length === 0) {
          delete relationships[relationship.sourceKey];
        }
      }
    },
    addMemory() {
      if (!this.new_memory || !this.new_memory.trim()) {
        return;
      }
      if (!Array.isArray(this.card.memories)) {
        this.card.memories = [];
      }
      this.card.memories.push(this.new_memory.trim());
      this.new_memory = '';
    }
  },
  computed: {
    relationshipMemoryEntries() {
      const relationships = this.card.relationship_memories;

      if (!relationships) {
        return [];
      }

      if (Array.isArray(relationships)) {
        return relationships.map((memory, index) => ({
          key: `relationship-${index}`,
          label: 'Relationship',
          memories: Array.isArray(memory) ? memory : [memory],
          sourceIndex: index,
          sourceKey: index
        }));
      }

      return Object.entries(relationships)
        .filter(([, memories]) => Array.isArray(memories))
        .map(([partner, memories]) => ({
          key: partner,
          label: partner || 'Relationship',
          memories,
          sourceIndex: null,
          sourceKey: partner
        }));
    },
    keywordsString: {
      get() {
        return Array.isArray(this.card.keywords) ? this.card.keywords.join(',') : this.card.keywords;
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
        <h3>
          <span class="card-name">{{ card.name }}</span>
          <span class="card-type">({{ card.type }})</span>
        </h3>
        <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
        <div v-if="!collapse">          
          <h4>Name</h4>
          <input type="text" v-model="card.name" maxlength="50" />

          <h4>Content</h4>
          <textarea v-model="card.content" />

          <div v-if="card.type === 'location'">
            <div>
              <label>Parent Location: </label>
              <input v-model="card.parent_location" maxlength="200" />
            </div>
            <div>
              <label>Child Locations: </label>
              <input v-model="card.child_locations" maxlength="300" />
            </div>
          </div>

          <h4>Keywords (comma-separated)</h4>
          <input type="text" v-model="keywordsString" maxlength="200" />

          <div v-if="card.type === 'character' || card.type === 'location'">
            <h3>Memories</h3>

            <label>
              Create Memories: 
            <input v-model="card.create_memories" type="checkbox" class="custom-checkbox" />
            </label>

            <div v-if="card.create_memories
              || (card.memories && card.memories.length > 0)" 
              class="memory-section"
            >

              <button type="button" @click="show_memories = !show_memories">
                {{ show_memories ? 'Hide Memories' : 'Show Memories' }}
              </button>

              <div v-if="show_memories" class="memory-list">
                <label>Keyword for memory creation: {{ card.keywords[0] }}.
                  <span title="The first set keyword will be used to create memories.">
                    ⓘ
                  </span>
                </label>

                <p v-if="!card.memories || card.memories.length === 0">
                  No memories.
                </p>

                <div
                  v-for="(memory, index) in card.memories"
                  :key="index"
                  class="memory-item"
                >
                  <label>Memory {{ index + 1 }}:
                    <input v-model="card.memories[index]" />
                    <button type="button" class="btn btn-danger" @click="removeMemory(index)">
                      Remove
                    </button>
                  </label>
                </div>

                <div v-if="relationshipMemoryEntries.length > 0">
                  <h4>Relationship Memories</h4>
                  <div
                    v-for="relationship in relationshipMemoryEntries"
                    :key="relationship.key"
                  >
                    <div
                      v-for="(memory, index) in relationship.memories"
                      :key="`${relationship.key}-${index}`"
                      class="memory-item"
                    >
                      <label>Memory {{ index + 1 }}:
                        <input v-model="relationship.memories[index]" />
                        <button type="button" class="btn btn-danger" @click="removeRelationshipMemory(relationship, index)">
                          Remove
                        </button>
                      </label>
                    </div>
                  </div>
                </div>

                <div class="add-memory-row">
                  <input
                    type="text"
                    v-model="new_memory"
                    placeholder="Add a new memory"
                    maxlength="200"
                  />
                  <button
                    type="button"
                    class="btn btn-primary"
                    @click="addMemory"
                  >
                    Add Memory
                  </button>
                </div>
              </div>
            </div>
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
.context-card h3 {
  position: relative;
  text-align: center;
  margin: 0;
}
.card-name {
  display: inline-block;
}
.card-type {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
  margin-right: 5px;
}
.context-card button {
  margin-bottom: 10px;
}
.memory-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.memory-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.memory-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.memory-item input {
  width: 70%;
}
.add-memory-row {
  display: flex;
  gap: 5px;
  align-items: center;
}
.add-memory-row input {
  flex: 1;
}
</style>
