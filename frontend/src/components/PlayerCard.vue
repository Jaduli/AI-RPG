<script>
export default {
  data() {
    return {
      collapse: false,
      name: '',
      information: ''
    }
  },
  methods: {
    reset() {
      this.name = '';
      this.information = '';
    },
    // Returns player name and information for saving
    getPlayer() {
      return {name: this.name, information: this.information};
    },
    // Returns string of player name and information to use in story generation
    getPlayerStr() {
      let str = '';

      if (this.name) {
        str += 'Player name: ' + this.name + '\n\n';
      }
      if (this.information) {
        str += 'Player information:\n' + this.information;
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
    <h2>Player Name</h2>
    <input 
      type="text" 
      v-model="name" 
      maxlength="50"
    />

    <h2>Player Information</h2>
    <textarea 
      v-model="information" 
      rows="10" 
      placeholder="E.g. age, looks, class, reputation. Always included in story context.">
    </textarea>
  </div>
</template>

<style>
.player-container {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
  margin-bottom: 10px;
}
.player-container h2 {
  margin: 10px 0 5px;
}
</style>