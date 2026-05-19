<script>
export default {
  data() {
    return {
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
    // Returns string of player name and description to use in context
    getPlayerStr() {
      let str = '';

      if (this.name) {
        str += 'Player name: ' + this.name + '\n\n';
      }
      if (this.description) {
        str += 'Player Description:\n' + this.description + '\n\n';
      }
      return str;  
    }
  }
}
</script>

<template>
    <h2>Player Name</h2>
    <input type="text" 
    v-model="name" 
    maxlength="50"/>

    <h2>Player Description</h2>
    <textarea 
    v-model="description" 
    rows="10" 
    cols="80" 
    placeholder="E.g. age, looks, class, reputation. Always included in story context.">
    </textarea>
</template>

<style>
input {
  margin-bottom: 30px;
}
</style>