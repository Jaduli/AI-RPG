<script>
export default {
  name: "Inventory",
  data() {
    return {
      inventory: [
        {
          id: 1,
          name: "Bronze Coins",
          value: 1,
          amount: 50,
          image: "https://pngimg.com/uploads/coin/coin_PNG36943.png",
        }
      ],
    };
  },
};
</script>

<template>
  <div class="inventory-container">
    <div
      v-for="item in inventory"
      :key="item.id"
      class="inventory-item"
    >
      <img
        :src="item.image"
        :alt="item.name"
        class="item-image"
      />

      <div class="item-details">
        <h3>{{ item.name }}</h3>
        <p>Amount: {{ item.amount }}</p>
        <p>Value: {{ item.value }} gold</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  padding: 20px;
  background: #1e1e1e;
}

.inventory-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #2c2c2c;
  border: 2px solid #444;
  border-radius: 12px;
  padding: 12px;
  color: white;
  transition: transform 0.2s ease;
}

.inventory-item:hover {
  transform: scale(1.03);
}

.item-image {
  width: 64px;
  height: 64px;
  object-fit: contain;
  background: #111;
  border-radius: 8px;
  padding: 4px;
}

.item-details h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.item-details p {
  margin: 2px 0;
  color: #ccc;
}
</style>