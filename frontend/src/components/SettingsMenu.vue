<script>
export default {
  data() {
    return {
      temp_context_length: this.context_length
    }
  },
  props: {
    gamemode: String,
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_local_toggle: Boolean,
    show_token_use: Boolean,
    top_p: Number,
    temperature: Number,
    max_tokens: Number,
    context_length: Number,
    is_loading: Boolean,
    summarize: Boolean,
    memorize: Boolean
  },
  methods: {
    setContextLength(new_length) {
      let num = Number(new_length);

      // Handle invalid input
      if (isNaN(num)) {
        num = this.context_length || 4000; // fallback
      } else {
        // Clamp to 1-32000
        num = Math.min(Math.max(num, 1), 32000);
      }
      this.temp_context_length = num;
      this.$emit('update:context_length', num);
    }
  },
  computed: {
    // Create computed properties with getters and setters to emit value updates
    gamemodeVal: {
      get() { return this.gamemode; },
      set(v) { this.$emit('update:gamemode', v); }
    },
    mainModelVal: {
      get() {
        return this.main_model;
      },
      set(v) {
        // Default to 'llama-3.1-8b-instant' if input is empty
        const value = v && v.trim() !== '' ? v : 'llama-3.1-8b-instant';
        this.$emit('update:main_model', value);
      }
    },
    memModelVal: {
      get() {
        return this.mem_model;
      },
      set(v) {
        // Default to 'llama-3.1-8b-instant' if input is empty
        const value = v && v.trim() !== '' ? v : 'llama-3.1-8b-instant';
        this.$emit('update:mem_model', value);
      }
    },
    localVal: {
      get() { return this.use_local; },
      set(v) { this.$emit('update:use_local', v); }
    },
    tokenVal: {
      get() { return this.show_token_use; },
      set(v) { this.$emit('update:show_token_use', v); }
    },
    summarizeVal: {
      get() { return this.summarize; },
      set(v) { this.$emit('update:summarize', v); }
    },
    memorizeVal: {
      get() { return this.memorize; },
      set(v) { this.$emit('update:memorize', v); }
    },
    topPVal: {
      get() { return this.top_p; },
      set(v) {
        let num = Number(v);

        // Handle invalid input
        if (isNaN(num)) {
          num = this.top_p || 0.9; // fallback
        } else {
          // Clamp to 0-1
          num = Math.min(Math.max(num, 0), 1);
        }
        this.$emit('update:top_p', num);
      }
    },
    temperatureVal: {
      get() { return this.temperature },
      set(v) {
        let num = Number(v);

        // Handle invalid input
        if (isNaN(num)) {
          num = this.temperature || 0.8; // fallback
        } else {
          // Clamp to 0-2
          num = Math.min(Math.max(num, 0), 2);
        }
        this.$emit('update:temperature', num);
      }
    },
    maxTokensVal: {
      get() { return this.max_tokens; },
      set(v) {
        let num = Number(v);

        // Handle invalid input
        if (isNaN(num)) {
          num = this.max_tokens || 200; // fallback
        } else {
          // Clamp to 10-1000
          num = Math.min(Math.max(num, 10), 1000);
        }
        this.$emit('update:max_tokens', num);
      }
    }
  }
}
</script>

<template>
  <div class="container modal-settings">
    <div class="modal-header">
      <h2>Settings</h2>
      <button class="close-btn" @click="$emit('close')" title="Close settings (ESC)">✕</button>
    </div>

    <label>Game Mode: 
      <select v-model="gamemodeVal">
        <option value="rpg">RPG</option>
        <option value="storyteller">Storyteller</option>
      </select>
    </label>

    <label>Main Model Name: 
      <input v-model="mainModelVal" 
      type="text" 
      placeholder="llama-3.1-8b-instant"
      />
    </label>

    <label v-if="show_local_toggle">Use Local AI: 
      <input v-model="localVal" type="checkbox" class="custom-checkbox" />
    </label>

    <label v-if="!use_local">Secondary Model Name: 
      <input v-model="memModelVal" 
      type="text" 
      placeholder="llama-3.1-8b-instant"
      />
      <span title="Secondary model will be used for context generation, e.g. for memories and asset creation.">
        ⓘ
      </span>
    </label>

    <label>Update Story Summary: 
      <input v-model="summarizeVal" type="checkbox" class="custom-checkbox" />
    </label>

    <label>Create Memories: 
      <input v-model="memorizeVal" type="checkbox" class="custom-checkbox" />
    </label>

    <label>Editor Token Limit: 
      <input 
        v-model.number="temp_context_length"
        type="number" 
        max="32000" 
        min="1"
        placeholder="4000"
      />
      <button @click="setContextLength(temp_context_length)" :disabled="is_loading">Set Limit</button>
    </label>

    <label>Top P: 
      <input v-model.number="topPVal" 
      type="number" 
      step="0.1" 
      min="0" 
      max="1"
      placeholder="0.9" />
    </label>

    <label>Temperature: 
      <input v-model.number="temperatureVal" 
      type="number" 
      step="0.1" 
      min="0" 
      max="2"
      placeholder="0.8" />
    </label>

    <label>Maximum Returned Tokens: 
      <input v-model.number="maxTokensVal" 
      type="number" 
      min="10"
      max="1000"
      placeholder="200" />
    </label>

    <label>Show API Call Token Usage: 
      <input v-model="tokenVal" type="checkbox" class="custom-checkbox" />
    </label>
  </div>
</template>

<style scoped>
.modal-settings {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-width: 500px;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #aa3bff;
}

.modal-header h2 {
  margin: 0;
  flex: 1;
}

.close-btn {
  background: transparent;
  border: none;
  color: #aa3bff;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(170, 59, 255, 0.2);
  color: #fff;
}
</style>