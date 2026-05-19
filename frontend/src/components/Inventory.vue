<script>
import InventoryItem from './InventoryItem.vue';

export default {
  data() {
    return {
      collapse: false,
      name: '',
      content: '',
      selected_type: 'all',
      type: 'other',
      equipped: false,
      inventory: []
    }
  },
  components: { InventoryItem },
  methods: {
    // Add item with id, name, content, keywords (comma separated),
    // and type-specific values.
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
    getInventoryStr(only_equipped = false) {
      if (this.inventory.length === 0) return '';

      let str = '';
      const grouped = {};

      // Sort inventory by group
      for (const item of this.inventory) {
        if (only_equipped && !item.equipped) continue;
        if (!grouped[item.type]) {
          grouped[item.type] = [];
        }
        grouped[item.type].push(item);
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
      return str;
    },
    removeItem(id) {
      this.inventory = this.inventory.filter(item => item.id !== id);
    },
    // Generate new item with local or cloud AI and add to Inventory
    async generateInventoryItem(type = 'other', name = '', context = '', equipped = false) {
      const parent = this.$parent;

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
            context: context
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
      if (this.selected_type !== 'all') {
        filtered = filtered.filter(item => item.type === this.selected_type);
      }
      return [...filtered].reverse();
    }
  }
}
</script>

<template>
  <div class="inventory">
    <h2>Add New Item</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>
    
    <div class="item" v-if="!collapse">
      <h4>Name</h4>
      <input type="text" v-model="name" maxlength="25" />
      
      <label>Item Type: 
        <select v-model="type">
          <option value="other">Other</option>
          <option value="perishable">Perishable</option>
          <option value="weapon">Weapon</option>
          <option value="apparel">Armor/apparel</option>
        </select>
      </label>

      <h4>Item Information</h4>
      <textarea v-model="content" />

      <label v-if="type !== 'perishable'">
        Equipped: 
        <input v-model="equipped" type="checkbox" class="custom-checkbox" />
        <span title="Equipped inventory will always be used in story context.">
          ⓘ
        </span>
      </label>

      <button @click="addItem">Add Item</button>
    </div>
    <div class="container">
      <h2>Inventory</h2>
      <label>Filter: 
        <select v-model="selected_type">
          <option value="all">All</option>
          <option value="perishable">Perishable</option>
          <option value="weapon">Weapon</option>
          <option value="apparel">Armor/apparel</option>
          <option value="other">Other</option>
        </select>
      </label>

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