<script>
import StoryEditor from './components/StoryEditor.vue';
import SettingsMenu from './components/SettingsMenu.vue';

export default {
  components: { StoryEditor, SettingsMenu },
  data() {
    return {
      // Default settings //

      // Mode determines which default prompt is used in story generation.
      // Currently available modes: 'rpg' and 'storyteller'
      gamemode: 'rpg',
      // Main model used for story continuation.
      main_model: 'llama-3.1-8b-instant', // Free model on Groq
      // Memory model used for memory and summary generation.
      mem_model: 'llama-3.1-8b-instant',
      // If true, memory and summary are generated with local AI.
      use_local: false, 
      // Shows/hides toggle depending on mode (local AI (=GPU mode)/no local AI).
      // Only shown if local AI is available, otherwise use_local is always false.
      show_local_toggle: false, 
      // If true, show total tokens used for all AI API calls (including local).
      show_token_use: false,
      // Context length affects the length of recent story
      // used as context in story generation (in tokens).
      context_length: 4000,
      // Top P and temperature control randomness in the AI output.
      // Higher values mean more randomness and creativity, lower values improve 
      // consistency with story context (e.g. story essentials and memories).
      top_p: 0.9,
      temperature: 1,
      // Max tokens controls the length of returned content in story generation.
      max_tokens: 150,
      memorize: true,
      summarize: true,
      show_settings: false,
      config_ready: false,
      story_is_loading: false
    }
  },
  methods: {
    closeSettings() {
      this.show_settings = false;
    },
    // Load backend config before starting the app. If backend is not ready, a new call
    // will be made every 2 seconds until a connection is made. This prevents frontend
    // errors due to backend being unavailable.
    async loadConfig(delay = 2000) {
      while (!this.config_ready) {
        try {
          const res = await fetch('/api/config');

          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }

          const data = await res.json();

          // If local AI is enabled, show toggle and set use_local to true by default.
          // Otherwise local AI features are disabled.
          this.show_local_toggle = data.local_ai_enabled;
          this.use_local = data.local_ai_enabled;
          
          // Load default models from backend .env if provided
          this.main_model = data.main_model || this.main_model;
          this.mem_model = data.mem_model || this.mem_model;

          this.gamemode = data.gamemode || this.gamemode;

          if (this.gamemode === 'storyteller') {
            max_tokens = 200; // Longer output is better for storytelling
          }

          this.config_ready = true;
        } catch (err) {
          console.error('Failed to load backend configuration, retrying...', err);
          await this.wait(delay);
        }
      }
    },
    wait(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  },
  async mounted() {
    // Load backend config
    this.loadConfig();
    // Add ESC key handler for closing modal
    window.addEventListener('keydown', this.handleEscKey);
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.handleEscKey);
  },
  handleEscKey(e) {
    if (e.key === 'Escape') {
      this.closeSettings();
    }
  }
}
</script>

<template>
  <!-- App is loaded only after backend config is ready -->
  <div v-if="config_ready" class="app-container">
    <div class="app-header">
      <h1>AI Storyteller</h1>
      <button @click="show_settings = !show_settings" class="settings-btn" title="Settings">
        ⚙️
      </button>
    </div>

    <StoryEditor class="story-editor"
      :gamemode="gamemode"
      :main_model="main_model"
      :mem_model="mem_model"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"
      :top_p="top_p"
      :temperature="temperature"
      :max_tokens="max_tokens"
      :summarize="summarize"
      :memorize="memorize"
      @loading-changed="story_is_loading = $event"
    />
    
    <!-- Settings Modal Backdrop -->
    <div v-if="show_settings" class="modal-backdrop" @click="closeSettings"></div>
    
    <!-- Settings Modal -->
    <div v-if="show_settings" class="modal-container">
      <SettingsMenu
      :gamemode="gamemode"
      :main_model="main_model"
      :mem_model="mem_model"
      :show_local_toggle="show_local_toggle"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"
      :top_p="top_p"
      :temperature="temperature"
      :max_tokens="max_tokens"
      :is_loading="story_is_loading"
      :summarize="summarize"
      :memorize="memorize"

      @update:gamemode="gamemode = $event"
      @update:main_model="main_model = $event"
      @update:mem_model="mem_model = $event"
      @update:use_local="use_local = $event"
      @update:show_token_use="show_token_use = $event"
      @update:context_length="context_length = $event"
      @update:top_p="top_p = $event"
      @update:temperature="temperature = $event"
      @update:max_tokens="max_tokens = $event"
      @update:summarize="summarize = $event"
      @update:memorize="memorize = $event"
      @close="closeSettings"
      />
    </div>
  </div>
  <div v-else>
    <p>Loading backend configuration, please wait...</p>
  </div>
</template>

<style>
/* Styling for app components */
input, textarea {
  resize: none;
  padding: 8px;
  margin: 3px;
  background: #0f0f1e;
  color: #fff;
  border: 1px solid #0f0f1e;
  border-radius: 3px;
  font-family: inherit;
  box-sizing: border-box;
}

textarea {
  font-family: 'Merriweather', 'Georgia', serif;
  width: 100%;
  margin-bottom: 10px;
  text-align: justify;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #aa3bff;
  box-shadow: 0 0 5px rgba(170, 59, 255, 0.3);
}

button {
  background: #aa3bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  margin: 5px;
}
button:disabled {
  background: #9a2bef;
  cursor: default;
  opacity: 0.7;
}
.btn-danger {
  background: #ff4d4d;
}

.container {
  border-radius: 5px;
  padding: 15px;
  background: #1a1a2e;
  margin: 5px;
}

.info-container {
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
  width: 80%;
  margin: 0 auto;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.2);
  padding-bottom: 4px;
  margin-bottom: 8px;
}

.custom-checkbox {
  accent-color: #aa3bff;
  cursor: pointer;
}

select {
  background: #0f0f1e;
  border: 1px solid #0f0f1e;
  color: #fff;
  border-radius: 3px;
  padding: 8px;
  cursor: pointer;
}

select:focus {
  outline: none;
  border: 1px solid #aa3bff;
  box-shadow: 0 0 5px rgba(170, 59, 255, 0.3);
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
}

.modal-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 999;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.app-header h1 {
  margin: 0;
  flex: 1;
}

.settings-btn {
  background: none;
  border: none;
  color: #aa3bff;
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  border-radius: 3px;
  transition: all 0.2s ease;
  position: relative;
  z-index: 1000;
}

.settings-btn:hover {
  background: rgba(170, 59, 255, 0.1);
  color: #fff;
}

.settings-btn:active {
  transform: scale(0.95);
}
</style>