<script>
export default {
  data() {
    return {
      name: '',
      description: ''
    }
  },
  props: {
    inventory: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    getPlayerStr() {
      var str = '';

      if (this.name) {
        str += 'Player name: ' + this.name + '\n\n';
      }
      if (this.description) {
        str += 'Player Description:\n' + this.description + '\n\n';
      }
      return str;  
    },
    formatType(type) {
      const capitalized = type.charAt(0).toUpperCase() + type.slice(1);

      // Keep 'apparel' non-plural
      return type === 'apparel' ? capitalized : capitalized + 's';
    }
  },
  computed: {
    sortedInventory() {
      const typeOrder = { 'perishable': 1, 'weapon': 2, 'apparel': 3, 'other': 4 };
      return [...this.inventory].sort((a, b) => {
        return (typeOrder[a.item_type] || 99) - (typeOrder[b.item_type] || 99);
      });
    },
    inventoryByType() {
      const grouped = {};
      for (const item of this.sortedInventory) {
        const type = item.item_type || 'other';
        if (!grouped[type]) {
          grouped[type] = [];
        }
        grouped[type].push(item);
      }
      return grouped;
    }
  }
}
</script>

<template>
  <div class="container">
      <h2>Name</h2>
      <input type="text" 
      v-model="name" 
      maxlength="20"/>

      <h2>Description</h2>
      <textarea 
      v-model="description" 
      rows="10" 
      cols="80" 
      placeholder="E.g. age, looks, class, reputation. Always included in story context.">
      </textarea>
  </div>
  <div class="container">
      <h2>Inventory</h2>
      <div v-if="inventory.length === 0" class="no-inventory">
        <p>No items</p>
      </div>
      <div v-else>
        <div v-for="(items, type) in inventoryByType" :key="type" class="inventory-category">
          <h4>{{ formatType(type) }}</h4>
          <div v-for="item in items" :key="item.id" class="inventory-item">
            <p>{{ item.name }}</p>
            <p>{{ item.content }}</p>
            <p class="equipped-text" v-if="item.equipped">(equipped)</p>
          </div>
        </div>
      </div>
  </div>
</template>

<style>
.no-inventory {
  color: #999;
  font-style: italic;
}

.inventory-category {
  margin-bottom: 15px;
}

.inventory-category h4 {
  color: #aa3bff;
  margin-bottom: 8px;
  border-bottom: 1px solid #aa3bff;
  padding-bottom: 5px;
}

.inventory-item {
  margin-left: 15px;
  margin-bottom: 10px;
  padding: 8px;
  background: #0f0f1e;
  border-radius: 3px;
  border-left: 2px solid #aa3bff;
}

.equipped-text {
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
}
</style>