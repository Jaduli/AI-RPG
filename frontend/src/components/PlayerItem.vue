<script>
export default {
  data() {
    return {
      collapse: true
    }
  },
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  emits: ['remove']
}
</script>

<template>
    <div class="item">
      <h3>
        <span class="item-name">{{ item.name }}</span>
        <span class="item-type">({{ item.type }})</span>
      </h3>

      <label v-if="item.type !== 'perishable'">
        Equipped: 
        <input v-model="item.equipped" type="checkbox" class="custom-checkbox" />
      </label>

      <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
      <div v-if="!collapse">          
        <h4>Name</h4>
        <input type="text" v-model="item.name" maxlength="25" />

        <h4>Content</h4>
        <textarea v-model="item.content" />

        <button class="btn btn-danger" @click="$emit('remove')">Discard Item</button>
      </div>
    </div>
</template>

<style>
.item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.item > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.item textarea {
  min-height: 50px;
}
.item h4 {
  margin: 3px 0 3px;
}
.item h3 {
  position: relative;
  text-align: center;
  margin: 0;
}
.item-name {
  display: inline-block;
}
.item-type {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
}
.item label {
  position: absolute;
  left: 0;
  top: 0;  
  font-size: 0.7em;
  font-weight: normal;
} 
.item button {
  margin-bottom: 10px;
}
</style>