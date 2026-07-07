<script>
import ContextCards from './ContextCards.vue';
import FileMenu from './FileMenu.vue';
import PlayerCard from './PlayerCard.vue';
import Inventory from './PlayerInventory.vue';
import Skills from './PlayerSkills.vue';
import ActionRow from './ActionRow.vue';

// Approximate to 4 characters per token for simple tokens-to-chars conversion.
// Real token amount may vary based on language and content.
const APPROX_CHARS_PER_TOKEN = 4;

export default {
  name: 'StoryEditor',
  components: {
    ContextCards,
    FileMenu,
    PlayerCard,
    Inventory,
    Skills,
    ActionRow
  },
  emits: ['loading-changed'],
  props: {
    // From SettingsMenu
    gamemode: String,
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_token_use: Boolean,
    context_length: Number,
    top_p: Number,
    temperature: Number,
    max_tokens: Number,
    summarize: Boolean,
    memorize: Boolean,
    generate_direction: Boolean,
  },
  data() {
    return {
      // Random story ID for storing memories in database.
      // Uses 32 bits (additional checks to prevent collision
      // may be required if used on a larger scale).
      story_id: crypto.getRandomValues(new Uint32Array(1))[0],
      // Components
      instructions: '', // Special instructions for the AI to use
      content: '',
      summary: '',
      story_direction: '',
      essential_context: '',
      editor_notes: '',
      notes_collapsed: true,
      sent_context: '', // Full context sent for story generation
      status_message: '',
      // Values
      story_name: '',
      active_tab: 'files',
      active_requests: 0,
      memory_cursor: 0,
      summary_cursor: 0,
      card_memory_cursor: 0,
      direction_turn_counter: 0,
      player_section: 'inventory',
      // Recent story content (i.e. content within the context window) 
      // is displayed in the editor
      story_editor_content: '',
      recent_action: '',
      recent_outcome: '',
      outcome_counter: 0
    }
  },
  methods: {
    setActiveTab(tab) {
      this.active_tab = tab;
    },
    // Extract past content between cursor and beginning of recent content,
    // i.e. content that has fallen out of the context window. Overlap with recent  
    // story can be added and is used in summarization to avoid losing context 
    // between summary actions.
    extractPastContent(cursor, overlap = 0) {
      const recent_story_window = this.context_length * APPROX_CHARS_PER_TOKEN;

      let cutoff_index = this.content.length - recent_story_window;

      // Overlap with recent content (default: no overlap)
      cutoff_index += overlap;

      // Ensure cutoff is not negative (e.g. when content length is less than context window allows)
      cutoff_index = Math.max(0, cutoff_index)

      // Past content window is between cursor and cutoff index
      const past_content = this.content.slice(cursor, cutoff_index);

      return {past_content, cutoff_index};
    },
    // Syncronize content with story editor, e.g. to include user edits before saving
    syncContentWithEditor() {
      const start = this.displayStart;

      // Avoid unnecessary assignment if contents match
      if (this.story_editor_content !== this.content.slice(start)) {
        this.content = this.content.slice(0, start) + this.story_editor_content;
      }
    },
    toggleNotesPanel() {
      this.notes_collapsed = !this.notes_collapsed;
    },
    // Main function to continue the story with backend API
    async continueStory() {
      const recent_story = this.story_editor_content

      // Basic validation to ensure there's enough content to continue from
      if (!recent_story || recent_story.trim().length < 20) {
        this.status_message = 'Error: Please enter enough story content to continue.';
        return;
      }
      try {
        this.active_requests++;

        // Sync content with editor for any user edits before continuing story
        this.syncContentWithEditor();

        // Get relevant context cards based on found keywords in recent story (as a string)
        const context_cards = this.$refs.contextCards.getMatchingContextCardsStr(recent_story);

        let essential_context = this.essential_context;

        if (this.editor_notes) {
          essential_context += '\n\n' + this.editor_notes
        }

        let payload = {
          story_id: this.story_id,
          gamemode: this.gamemode,
          model: this.main_model,
          instructions: this.instructions,
          summary: this.summary,
          story_direction: this.story_direction,
          essential_context,
          context_cards,
          recent_story,
          top_p: this.top_p,
          temperature: this.temperature,
          max_tokens: this.max_tokens
        }

        let is_new_action = false;
        let player_action = '';
        let action_type = '';
        let selected_item = null;
        let selected_skill = null;
        let outcome = '';
        let use_d20 = false;

        // Get RPG elements if relevant
        if (this.gamemode === 'rpg') {
          // Get player action. If action is set to 'new', also generates
          // a new asset with most recent story as context if relevant.
          const action = await this.$refs.actionRow.getPlayerAction();

          is_new_action = action !== null;

          if (is_new_action) {
            player_action = action.player_action || '';
            selected_item = action.selected_item || null;
            selected_skill = action.selected_skill || null;
            use_d20 = action.use_d20 || false;
            action_type = action.action_type || '';
          }

          // Get skill outcome based on level if a skill was selected for the action
          if (selected_skill) {
            outcome = this.$refs.skills.getSkillOutcome(selected_skill.level);
          }

          // Reset previous action context when a new action is provided
          if (is_new_action) {
            this.recent_action = '';
            this.recent_outcome = '';
            this.outcome_counter = 0;
          }

          // Get player information (as string)
          const player_information = this.$refs.playerCard.getPlayerStr();
          const player_equipment = this.$refs.inventory.getEquipmentStr(selected_item);
          const player_skills = this.$refs.skills.getSkillsStr();

          const rpg_payload = {
            player_information,
            player_equipment,
            player_skills,
            player_action,
            outcome,
            player_item: selected_item ? selected_item.name : '',
            player_skill: selected_skill ? selected_skill.name : '',
            recent_action: this.recent_action,
            recent_outcome: this.recent_outcome,
            use_d20
          }

          // Merge payloads
          payload = { ...payload, ...rpg_payload };
        }

        this.status_message = 'Continuing story...';

        // Use POST for continue action
        const res = await fetch('/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error continuing story: ' + data.error;
          return;
        }

        const continued_content = data.continued_content || '';

        if (continued_content.trim() === '') {
          this.status_message = 'Error: Continue action returned empty content.';
          return;
        }

        // Append new content to story with proper spacing (\n\n + new content).
        // Count existing newlines at end of text
        const matching_count = recent_story.match(/\n*$/)[0].length;

        // Add 0-2 newlines based on existing count. This ensures \n\n in case of
        // 0-2 existing newlines but does not remove newlines above the limit.
        const newline_count = Math.max(0, 2 - matching_count);
        this.content += '\n'.repeat(newline_count);

        // Sync content with player action
        if (is_new_action) {
          this.content += player_action + '\n\n';
        }

        this.content += continued_content;
        
        // Display full context used in API call
        if (data.full_context) {
          this.sent_context = data.full_context;
        }

        if (this.gamemode === 'rpg') {
          // D20 action outcome of player action (success, failure, etc.)
          if (data.outcome) {
            this.recent_action = player_action;
            this.recent_outcome = data.outcome;
          }
          // Skill use outcome separate from D20
          if (outcome) {
            this.recent_action = player_action;
            this.recent_outcome = outcome;
          }

          // Add XP to used skill (allows leveling up).
          // Outcome affects xp multiplier.
          if (selected_skill) {
            this.$refs.skills.addSkillXp(selected_skill.id, outcome);
          }

          // Use action/outcome context for a maximum of 3 turns.
          // This allows actions that have not yet completed to
          // retain the same outcome.
          if (this.recent_action) {
            this.outcome_counter++;
          }
          if (this.outcome_counter >= 3) {
            this.recent_outcome = '';
            this.recent_action = '';
            this.outcome_counter = 0;
          }

          // Clear action after use without resetting selected item or action type.
          // This allows player to easily make another action of the same type.
          this.$refs.actionRow.reset(false);

          // Remove perishable items after use
          if (action_type === 'use' && selected_item && selected_item.type === 'perishable') {
            this.$refs.inventory.removeItem(selected_item.id);
          }
        }

        // Scroll to bottom to show new content
        this.$nextTick(() => {
          const el = this.$refs.editorBox;
          el.scrollTop = el.scrollHeight;
        });

        this.status_message = '';

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for continue action: ' + data.tokens_total;
        }

        // The following memory actions happen only if enough content has fallen out of the  
        // context window to avoid unnecessary API calls and to ensure that there is enough
        // content for the memory to be meaningful.

        // Summarize story
        if (this.summarize) {
          await this.summarizeStory();
        }

        // Turn past story content into a memory
        if (this.memorize) {
          await this.createMemory();
        }

        // Create memories for cards with memory creation enabled
        await this.createContextCardMemories();

        // Refresh future story direction every 15 turns when enabled.
        if (this.generate_direction) {
          this.direction_turn_counter += 1;

          if (this.direction_turn_counter >= 15) {
            await this.generateStoryDirection();
            this.direction_turn_counter = 0;
          }
        }

        // Automatically save the story with new content
        await this.saveStory();
      } catch (err) {
        this.status_message = 'Error continuing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to summarize the story with backend API
    async summarizeStory() {
      // Minimum past content length (in characters) to create a new summary.
      // default: 5000
      const minimum_length_chars = 5000;
      // Use half of minimum length as overlap with recent story.
      // This prevents context that falls out of recent content window
      // from being lost between summary actions.
      const overlap = minimum_length_chars / 2;

      let {past_content, cutoff_index} = this.extractPastContent(this.summary_cursor, overlap);

      const content_length = past_content.length;

      // Return if there is not enough content to memorize
      if (content_length < minimum_length_chars) {
        return;
      }
      // Prevent including too much content at once. Prioritize using newest story content.
      if (content_length > 10000) {
        past_content = past_content.slice(-10000);
      }
      try {
        this.active_requests++;
        this.status_message = 'Summarizing story, please wait...'

        const full_context = 'Current Summary:\n' + this.summary + 
                             '\n\nNew Story Content:\n' + past_content;
        
        // Use POST for summary action
        const res = await fetch('/api/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: full_context,
            model: this.mem_model,
            local: this.use_local
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error summarizing story: ' + data.error;
          return;
        }
        if (!data.summary || data.summary.trim() === '') {
          this.status_message = 'Error: Summary action returned empty content.';
          return;
        }

        this.summary = data.summary;
        this.status_message = '';
        
        // Move summary cursor forward to cutoff index for next summary action
        this.summary_cursor = cutoff_index;

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for summary action: ' + data.tokens_total;
        }
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to create a memory with backend API
    async createMemory() {
      // Minimum past content length to create a new memory.
      // default: 8000
      const minimum_length_chars = 8000;

      // Use past story content for new memory (without overlap with recent story)
      let {past_content, cutoff_index} = this.extractPastContent(this.memory_cursor);

      const content_length = past_content.length;

      // Return if there is not enough content to memorize
      if (content_length < minimum_length_chars) {
        return;
      }
      // Prevent including too much content at once. Prioritize using newest story content.
      if (content_length > 10000) {
        past_content = past_content.slice(-10000);
      }
      try {
        this.active_requests++;
        this.status_message = 'Creating a new memory, please wait...'
        
        // Use POST for memory action
        const res = await fetch('/api/memorize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            story_id: this.story_id,
            content: 'Past Story Content:\n' + past_content,
            model: this.mem_model,
            local: this.use_local
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error creating memory: ' + data.error;
          return;
        }
        this.status_message = '';

        // Move memory cursor forward to cutoff index for next memory creation
        this.memory_cursor = cutoff_index;

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for memory action: ' + data.tokens_total;
        }
      } catch (err) {
        this.status_message = 'Error creating memory: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to create context card memories with backend API. This extracts relevant 
    // character and location information from past story content and creates new context 
    // card memories for them.
    async createContextCardMemories() {
      try {
        // Minimum past content length to create a card new memory.
        // default: 1000
        const minimum_length_chars = 1000;

        // Use past story content for new card memory (without overlap with recent story)
        let {past_content, cutoff_index} = this.extractPastContent(this.card_memory_cursor);

        const content_length = past_content.length;

        // Return if there is not enough content to memorize
        if (content_length < minimum_length_chars) {
          return;
        }
        // Prevent including too much content at once. Prioritize using newest story content.
        if (content_length > 2000) {
          past_content = past_content.slice(-2000);
        }

        // Create new memory for one relevant character + location found in
        // past story content (if memory creation is enabled). Uses a random
        // chance based on existing memory count.
        await this.$refs.contextCards.addCardMemory(past_content, 'character');
        await this.$refs.contextCards.addCardMemory(past_content, 'location');

        this.card_memory_cursor = cutoff_index;
      } catch (err) {
        console.error('Error creating context card memory: ' + (err.message || err));
      }
    },
    // Trigger story direction generation from the current story editor content.
    async generateDirectionManually() {
      await this.generateStoryDirection();
    },
    // Function to generate AI story direction using essential context, summary, and recent story.
    async generateStoryDirection() {
      const recent_story = (this.story_editor_content || this.content.slice(this.displayStart)).slice(-5000).trim();

      if (!recent_story) {
        this.status_message = 'Error: Not enough recent story content to generate direction.';
        return;
      }

      const context_cards = this.$refs.contextCards?.getMatchingContextCardsStr(recent_story) || '';

      let player_information = '';

      if (this.gamemode === 'rpg') {
        player_information = this.$refs.playerCard.getPlayerStr();
      }

      try {
        this.active_requests++;
        this.status_message = 'Generating story direction, please wait...';

        const res = await fetch('/api/generate_direction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            instructions: this.instructions || '',
            essential_context: this.essential_context || '',
            summary: this.summary || '',
            context_cards: context_cards || '',
            player_information,
            recent_story,
            model: this.mem_model,
            local: this.use_local
          })
        });

        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error generating story direction: ' + data.error;
          return;
        }

        this.story_direction = data.direction || '';
        this.status_message = '';

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for story direction generation: ' + data.tokens_total;
        }
      } catch (err) {
        this.status_message = 'Error generating story direction: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to save the story to backend API
    async saveStory(sync = true) {
      // Only change status message if this is the only active request to
      // avoid confusion with other actions.
      const only_active = this.active_requests === 0;
      if (only_active) {
        this.status_message = 'Saving story...';
      }
      try {
        this.active_requests++;

        if (sync) {
          // Sync content with story editor before saving
          this.syncContentWithEditor();
        }
        
        const context_cards = this.$refs.contextCards.cards || [];

        let player_information = [];
        let player_inventory = [];
        let player_skills = [];

        if (this.gamemode === 'rpg') {
          player_information = this.$refs.playerCard.getPlayer() || [];
          player_inventory = this.$refs.inventory.getInventory() || [];
          player_skills = this.$refs.skills.getSkills() || [];
        }

        // Use POST to save story
        const res = await fetch('/api/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            story_id: this.story_id,
            story_name: this.story_name,
            instructions: this.instructions,
            content: this.content,
            summary: this.summary,
            story_direction: this.story_direction,
            essential_context: this.essential_context,
            editor_notes: this.editor_notes,
            memory_cursor: this.memory_cursor,
            summary_cursor: this.summary_cursor,
            card_memory_cursor: this.card_memory_cursor,
            context_cards,
            player_information,
            skills: player_skills,
            inventory: player_inventory
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error saving story: ' + data.error;
          return;
        }
        if (only_active && data.message) {
          this.status_message = 'Success: ' + data.message;
        }
        if (!data.error) {
          this.$refs.fileMenu.fetchFiles();
        }
      } catch (err) {
        this.status_message = 'Error saving story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to load the story from backend API
    async loadStory(story_id = null) {
      try {
        this.active_requests++;
        this.status_message = 'Loading story...';

        const id = story_id;
        if (!id) {
          this.status_message = 'Error loading file: Story ID missing.';
          return;
        }

        const res = await fetch('/api/load?story_id=' + encodeURIComponent(id));
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend load error: ' + data.error;
          return;
        }

        this.story_id = Number(id);
        this.story_name = data.story_name || '';
        this.instructions = data.instructions || '';
        this.content = data.content || '';
        this.summary = data.summary || '';
        this.story_direction = data.story_direction || '';
        this.essential_context = data.essential_context || '';
        this.editor_notes = data.editor_notes || '';
        this.memory_cursor = data.memory_cursor || 0;
        this.summary_cursor = data.summary_cursor || 0;
        this.card_memory_cursor = data.card_memory_cursor || 0;
        this.$refs.contextCards.cards = data.context_cards || [];
        this.recent_action = '';
        this.recent_outcome = '';
        this.outcome_counter = 0;

        // Expand notes field if used in save
        if (this.editor_notes) {
          this.notes_collapsed = false;
        }

        if (this.gamemode === 'rpg') {
          this.$refs.inventory.inventory = data.inventory || [];
          this.$refs.skills.skills = data.skills || [];

          // Get player information
          const player_information = data.player || [];
          this.$refs.playerCard.name = player_information.name || '';
          this.$refs.playerCard.information = player_information.information || '';

          // Reset ActionRow
          this.$refs.actionRow.reset();
        }

        // Scroll to bottom after loading story
        this.$nextTick(() => {
          const el = this.$refs.editorBox;
          el.scrollTop = el.scrollHeight;
        });
        this.status_message = 'Story loaded successfully.';
      } catch (err) {
        this.status_message = 'Error loading story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Create a new story with random ID and empty fields
    async createNewStory() {
      this.story_id = crypto.getRandomValues(new Uint32Array(1))[0];
      this.story_name = this.story_name || '';
      this.instructions = '';
      this.content = '';
      this.summary = '';
      this.story_direction = '';
      this.essential_context = '';
      this.editor_notes = '';
      this.notes_collapsed = true;
      this.memory_cursor = 0;
      this.summary_cursor = 0;
      this.$refs.contextCards.cards = [];
      this.recent_action = '';
      this.recent_outcome = '';
      this.outcome_counter = 0;
      this.card_memory_cursor = 0;
      this.direction_turn_counter = 0;

      if (this.gamemode === 'rpg') {
        this.$refs.inventory.inventory = [];
        this.$refs.skills.skills = [];
        
        // Reset player information
        this.$refs.playerCard.reset();   

        // Reset ActionRow
        this.$refs.actionRow.reset();
      }

      this.status_message = 'New story initialized with ID '  + this.story_id + '.';
    }
  },
  computed: {
    // App state counts as loading if any active request is in process.
    // This disables continue, save, and load buttons to prevent multiple simultaneous 
    // requests which could cause issues. Also disables 'Set Limit' button in settings 
    // menu when loading.
    isLoading() {
      return this.active_requests > 0;
    },
    // Calculate where to start displaying content in editor based on context length.
    // This prevents editing already memorized or summarized content and makes textEditor
    // more responsive by not rendering the entire story in the editor.
    displayStart() {
      const max_chars = this.context_length * APPROX_CHARS_PER_TOKEN;

      return Math.max(0, this.content.length - max_chars);
    },
  },
  watch: {
    // Update story_editor_content when content changes, e.g. when continuing or loading story
    content() {
      const start = this.displayStart;
      this.story_editor_content = this.content.slice(start);
    },
    // Emit loading change events so parent can disable settings controls when requests are active
    isLoading(value) {
      this.$emit('loading-changed', value);
    },
    // Watch for changes in context_length to ensure that content isn't lost when changing 
    // context window size and that the story editor properly reflects the new context window.
    context_length(new_val, old_val) {
      // Prevent unnecessary triggers
      if (new_val === old_val) return;

      try {
        const old_max_chars = old_val * APPROX_CHARS_PER_TOKEN;
        const old_start = Math.max(0, this.content.length - old_max_chars);

        // Sync content with editor using old start to avoid losing user edits
        if (this.story_editor_content !== this.content.slice(old_start)) {
          this.content = this.content.slice(0, old_start) + this.story_editor_content;
        }

        // Sync editor to display story content with new context length
        const new_start = this.displayStart;
        this.story_editor_content = this.content.slice(new_start);

        this.status_message = 'Limit set. Editor updated with new token limit.';
      } catch (err) {
        this.status_message = 'Error setting token limit: ' + (err.message || err);
      }
    }
  }
}
</script>

<template>
  <div class="tab-header">

  <button 
    :class="{ active: active_tab === 'files' }"
    @click="setActiveTab('files')"
  >
    Save Files
  </button>

  <button 
    :class="{ active: active_tab === 'story_context' }"
    @click="setActiveTab('story_context')"
  >
    Story Context
  </button>

  <button 
    :class="{ active: active_tab === 'editor' }"
    @click="setActiveTab('editor')"
  >
    Editor
  </button>

  <button 
    v-if="gamemode === 'rpg'"
    :class="{ active: active_tab === 'player' }"
    @click="setActiveTab('player')"
  >
    Player
  </button>

  <button 
    :class="{ active: active_tab === 'context_cards' }"
    @click="setActiveTab('context_cards')"
  >
    Context Cards
  </button>

  <button 
    :class="{ active: active_tab === 'sent_context' }"
    @click="setActiveTab('sent_context')"
  >
    Sent Context
  </button>
  </div>

  <div class="tab-content">
    <div v-show="active_tab === 'files'">
      <div class="container">
        <h2>Story Title</h2>
        <input v-model="story_name" 
        placeholder="Story name"
        maxlength="30" />
        <button @click="saveStory" :disabled="isLoading">Save Story</button>
        <button @click="createNewStory" :disabled="isLoading">Create New Story</button>
      </div>
      <p class="status">{{ status_message }}</p>
      <FileMenu
        ref="fileMenu" 
        :story_id="story_id" 
        :is_loading="isLoading"
        @load-file="loadStory"
      />
    </div>

    <div v-show="active_tab === 'story_context'">
      <div class="container">
        <h2>Generation Instructions</h2>
        <textarea 
        v-model="instructions" 
        rows="10" 
        cols="80" 
        placeholder="Additional story generation instructions can be added here.">
        </textarea>
      </div>
      <div class="container">
        <h2>Essential Context</h2>
        <textarea v-model="essential_context" 
        rows="10" 
        cols="80" 
        placeholder="Key plot points, character details, or world-building elements. This will always be used as context in story generation.">
        </textarea>
      </div>
      <div class="container">
        <h2>Story Summary</h2>
        <textarea v-model="summary" 
        rows="10" 
        cols="80" 
        placeholder="Summary will appear here. Summary will be used as context in story generation.">
        </textarea>
      </div>
      <div class="container">
        <h2>Future Story Direction</h2>
        <textarea v-model="story_direction" 
        rows="10" 
        cols="80" 
        placeholder="Generated story direction will appear here.">
        </textarea>
        <button @click="generateDirectionManually" :disabled="isLoading">Generate Story Direction</button>
      </div>
    </div>

    <div v-show="active_tab === 'editor'">
      <div class="container">
        <h2>Story Editor</h2>
        <div class="editor-layout">
          <div class="editor-main">
            <textarea 
            ref="editorBox"
            v-model="story_editor_content" 
            rows="12" 
            cols="80" 
            placeholder="Paste or write story text here.">
            </textarea>
          </div>
          <div class="notes-panel" :class="{ collapsed: notes_collapsed }">
            <button class="toggle-notes" @click="toggleNotesPanel">
              {{ notes_collapsed ? '📝' : 'Hide Notes' }}
            </button>
            <textarea
              v-if="!notes_collapsed"
              v-model="editor_notes"
              rows="9"
              cols="30"
              placeholder="Add additional story notes/context here, e.g. current location or date.">
            </textarea>
          </div>
        </div>
        <ActionRow
          ref="actionRow"
          v-if="gamemode === 'rpg'"
          :gamemode="gamemode"
          :is_loading="isLoading"
        />
      </div>
      <p class="status">{{ status_message }}</p>
      <button @click="continueStory" :disabled="isLoading">Continue Story</button>
    </div>

    <div class="container" v-show="active_tab === 'context_cards'">
      <ContextCards
        ref="contextCards"
        :mem_model="mem_model"
        :use_local="use_local"
        :is_loading="isLoading"
      />
    </div>

    <div class="container" v-show="active_tab === 'player'">
      <PlayerCard ref="playerCard" />

      <div class="subtab-header">
        <button
          :class="{ active: player_section === 'inventory' }"
          @click="player_section = 'inventory'"
        >
          Inventory
        </button>
        <button
          :class="{ active: player_section === 'skills' }"
          @click="player_section = 'skills'"
        >
          Skills
        </button>
      </div>
      
      <div v-show="player_section === 'inventory'">
        <Inventory ref="inventory" />
      </div>
      <div v-show="player_section === 'skills'">
        <Skills ref="skills" />
      </div>
    </div>

    <div class="container" v-show="active_tab === 'sent_context'">
      <h2>Sent Context</h2>
      <textarea v-model="sent_context" 
      rows="12" 
      cols="80" 
      placeholder="Context sent to story generation will appear here."
      readonly>
      </textarea>
      <div class="tab-footer-space"></div>
    </div>
  </div>
</template>

<style scoped>
.status  {
  background: #0f0f1e;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 40px;
}

.editor-layout {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.editor-main {
  flex: 1;
  min-width: 0;
}

.editor-main textarea,
.notes-panel textarea {
  width: 100%;
  box-sizing: border-box;
}

.notes-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 280px;
  min-width: 280px;
}

.notes-panel.collapsed {
  width: auto;
  min-width: 0;
}

.toggle-notes {
  background: #aa3bff;
  padding: 6px 10px;
  cursor: pointer;
}

.tab-content {
  position: relative;
  padding-top: 10px;
}

.tab-header button,
.subtab-header button {
  background: #1a1a2e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  margin: 0px;
}

.subtab-header button {
  border: 1px solid #9a2bef;
}

.tab-header button:hover,
.subtab-header button:hover {
  background: #aa3bff;
}
.tab-header button.active,
.subtab-header button.active {
  background: #9a2bef;
  color: white;
  font-weight: bold;
}
</style>
