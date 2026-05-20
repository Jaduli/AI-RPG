<script>
export default {
  data() {
    return {
      collapse: false,
      name: '',
      description: ''
    }
  },
  methods: {
    reset() {
      this.name = '';
      this.description = '';
    },
    // Returns player name and description for saving
    getPlayer() {
      return {name: this.name, description: this.description};
    },
    // Returns string of player name and description to use in story generation
    getPlayerStr() {
      let str = '';

      if (this.name) {
        str += 'Player name: ' + this.name + '\n\n';
      }
      if (this.description) {
        str += 'Player Description:\n' + this.description;
      }
      return str;  
    }
  }
}
</script>

<template>
  <div class="header-row">
    <h2>Player Information</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>
  </div>

  <div v-if="!collapse" class="player-container">
    <h2>Name</h2>
    <input 
      type="text" 
      v-model="name" 
      maxlength="50"
    />

    <h2>Description</h2>
    <textarea 
      v-model="description" 
      rows="10" 
      cols="80" 
      placeholder="E.g. age, looks, class, reputation. Always included in story context.">
    </textarea>
  </div>
</template>

<style>
.player-container {
  border: 1px solid #aa3bff;
  margin-bottom: 10px;
}
.player-container h2 {
  margin-top: 10px;
}
</style>