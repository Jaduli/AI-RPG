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
        <h3>{{ item.name }} <span class="item-type">({{ item.type }})</span></h3>
        <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
        <div v-if="!collapse">          
          <h4>Name</h4>
          <input type="text" v-model="item.name" maxlength="25" />

          <h4>Content</h4>
          <textarea v-model="item.content" />

          <div>
            <label>Equipped: </label>
            <input v-model="item.equipped" type="checkbox" class="custom-checkbox" />
            <span title="Equipped items will always be used in story context.">
              ⓘ
            </span>
          </div>

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
  min-height: 120px;
}
.item h4 {
  margin: 3px 0 3px;
}
.item button {
  margin-bottom: 10px;
}
.item-type {
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
}
</style>