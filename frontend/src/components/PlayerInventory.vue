<script>
import InventoryItem from './PlayerItem.vue';

export default {
  data() {
    return {
      collapse: false,
      name: '',
      content: '',
      filter_type: 'all',
      type: 'other',
      equipped: false,
      inventory: []
    }
  },
  components: { InventoryItem },
  methods: {
    // Add item with id, name, type, content, and equipped value
    addItem() {
      const type = this.type

      // Perishables cannot be equipped, only used
      if (type === 'perishable') {
        this.equipped = false;
      }
      let payload = {
        id: Date.now(),
        name: this.name,
        type: type,
        content: this.content,
        equipped: this.equipped
      };
      this.inventory.push(payload);
      this.name = '';
      this.content = '';
    },
    getInventory() {
      return this.inventory;
    },
    // Gets equipment as string formatted for story context.
    // Item used by player is also added as context.
    getEquipmentStr(used_item = null) {
      if (this.inventory.length === 0) return '';

      let str = '';
      const grouped = {};

      // Sort equipped items by group
      for (const item of this.inventory) {
        if (item.equipped || (used_item && item.id === used_item.id)) {
          if (!grouped[item.type]) {
            grouped[item.type] = [];
          }
          grouped[item.type].push(item);
        }
      }

      for (const [type, items] of Object.entries(grouped)) {
        const title = type === 'apparel'
          ? 'Apparel' // Leave apparel non-plural
          : type.charAt(0).toUpperCase() + type.slice(1) + 's';

        str += title + '\n';

        for (const item of items) {
          str += `- ${item.name}: ${item.content}\n`;
        }
        str += '\n';
      }
      return str.trim();
    },
    removeItem(id) {
      this.inventory = this.inventory.filter(item => item.id !== id);
    },
    // Generate new item with local or cloud AI and add to Inventory
    async generateInventoryItem(type = 'other', name = '', recent_story = '', equipped = false) {
      const parent = this.$parent;
      const story_information = parent.essential_context;
      
      this.name = name;
      this.type = type;
      this.equipped = equipped;

      try {
        const res = await fetch('/api/generate_asset', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: parent.mem_model,
            local: parent.use_local,
            type: 'item',
            name: name,
            story_information: story_information,
            recent_story
          })
        });
        const data = await res.json();

        if (data.error) {
          throw new Error(data.error);
        }
        if (!data.generated_content) {
          throw new Error('Backend returned empty item content.');
        }
        this.content = data.generated_content;

        this.addItem();
      } catch (err) {
        throw new Error(err.message || err);
      } finally {
        this.loading = false;
      }
    },
  },
  computed: {
    // Display inventory from newest to oldest, filtered by selected type
    sortedItems() {
      let filtered = this.inventory;
      if (this.filter_type !== 'all') {
        filtered = filtered.filter(item => item.type === this.filter_type);
      }
      return [...filtered].reverse();
    }
  }
}
</script>

<template>
  <div class="header-row">
    <h2>Add Inventory Item</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>
  </div>

  <div class="container">    
    <div class="item" v-if="!collapse">
      <h4>Item Name</h4>
      <input type="text" v-model="name" maxlength="25" />
      
      <label>Type: 
        <select v-model="type">
          <option value="other">Other</option>
          <option value="perishable">Perishable</option>
          <option value="weapon">Weapon</option>
          <option value="apparel">Armor/apparel</option>
        </select>
        <span v-if="type === 'perishable'"
          title="Perishable items will only be included in context when used, and they will be discarded automatically after use.">
          ⓘ
        </span>
      </label>

      <h4>Item Information</h4>
      <textarea v-model="content" />

      <label v-if="type !== 'perishable'">
        Equipped: 
        <input v-model="equipped" type="checkbox" class="custom-checkbox" />
        <span title="Equipped items will always be included in context in story generation.">
          ⓘ
        </span>
      </label>

      <button @click="addItem">Add Item</button>
    </div>
  </div>

  <div class="container">
    <div class="header-row">
      <h2>Inventory</h2>
      <label>Filter: 
        <select v-model="filter_type">
          <option value="all">All</option>
          <option value="perishable">Perishable</option>
          <option value="weapon">Weapon</option>
          <option value="apparel">Armor/apparel</option>
          <option value="other">Other</option>
        </select>
      </label>
    </div>

    <p v-if="sortedItems.length === 0">
      No Items.
    </p>

    <InventoryItem
      v-for="item in sortedItems"
      :key="item.id"
      :item="item"
      @remove="removeItem(item.id)"
    />
  </div>
</template>

<style>
.inventory {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.inventory > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.item {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
}
.item h4 {
  margin: 3px 0 3px;
}
.item textarea {
  min-height: 120px;
}
.item button {
  margin-bottom: 10px;
}
</style>