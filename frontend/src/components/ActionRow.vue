<script>
export default {
  data() {
    return {
      loading: false,
      use_d20: false,
      action_type: 'custom',
      user_input: '',
      selected_item: null,
      new_asset_type: 'other',
      new_character_memories: true,
      new_item_type: 'other',
      new_item_equipped: false,
      input_placeholder: 'Input action'
    };
  },
  props: {
    gamemode: String,
  },
  methods: {
    // Reset values (all or just input)
    reset(all = true) {
      this.user_input = '';

      // D20 is generally not used two times consequently
      this.use_d20 = false;
      
      if (all) {
        this.action_type = 'custom';
        this.selected_item = null;
        this.new_asset_type = 'other';
        this.new_item_type = 'other';
        this.new_item_equipped = false;
      }
    },
    // Edits dialogue from first person to second person. This allows
    // RPG-style gameplay for user actions (e.g. "I open the door")
    // while keeping the story itself in second person.
    firstToSecondPerson(text) {
      // Split while keeping quoted text (dialogue) unedited
      const parts = text.split(/(".*?")/g);

      return parts.map(part => {
        // Skip quoted dialogue
        if (part.startsWith('"') && part.endsWith('"')) {
          return part;
        }

        // Replace first person with second person
        return part
          // contractions / phrases
          .replace(/\bI am\b/gi, 'you are')
          .replace(/\bI'm\b/gi, "you're")
          .replace(/\bI was\b/gi, 'you were')
          .replace(/\bI'd\b/gi, "you'd")
          .replace(/\bI'll\b/gi, "you'll")
          .replace(/\bI've\b/gi, "you've")

          // pronouns
          .replace(/\bI\b/gi, 'you')
          .replace(/\bme\b/gi, 'you')
          .replace(/\bmy\b/gi, 'your')
          .replace(/\bmine\b/gi, 'yours')
          .replace(/\bmyself\b/gi, 'yourself');
      }).join('');
    },
    // Formats user action to be appropriate for story generation
    getFormattedAction() {
      const type = this.action_type;
      let user_input = this.user_input.trim();

      // RPG elements added only if gamemode is rpg.
      if (this.gamemode !== 'rpg') {
        return user_input;
      }

      const item = this.selected_item;

      // If item is selected without a user action, fallback to general
      // use item message.
      if (type === 'use' && item && !user_input) {
        return `You use item '${item.name}'.`
      }
      // Otherwise if user input is empty, continue the story without an action
      if (!user_input) {
        return '';
      }

      // If action is new, story is continued with appropriate
      // user action for given story asset.
      if (type === 'new') {
        asset_type = this.new_asset_type;
        
        if (asset_type === 'inventory item') {
          if (this.new_item_equipped) {
            return `You equip item '${user_input}'.`
          }
          return `You get item '${user_input}'.`
        }
        if (asset_type === 'item') {
          `You learn about an item called '${user_input}'.`
        }
        if (asset_type === 'location' || asset_type === 'character') {
          `You learn about a ${asset_type} called ${user_input}.`
        }
        return `You learn about ${user_input}.`
      }

      // The following edit user input directly.

      // Add punctuation if missing
      if (!/[.!?"]$/.test(user_input)) {
        user_input += '.';
      }

      if (type === 'say') {
        // Add quotes to dialogue
        if (!user_input.endsWith('"') || !user_input.startsWith('"')) {
          user_input = '"' + user_input + '"'
        }
        return 'You say ' + user_input;
      }

      if (type === 'do') {
        // Add "You" if missing (e.g. 'open the door -> You open the door')
        if (!/^you\b/i.test(action.trim())) {
          return 'You ' + user_input;
        }
      }

      // Capitalize first letter
      user_input = user_input.charAt(0).toUpperCase() + user_input.slice(1);

      return user_input;
    },
    // Returns formatted player action and values for selected item, D20 toggle,
    // and action type.
    async getPlayerAction() {
      if (this.action_type === 'new') {
        // Create new asset before continuing the story
        const cont = await this.createNewAsset();

        // Return if errors occur during asset generation.
        if (!cont) return;
      }

      let item = null;
      if (this.action_type === 'use') {
        item = this.selected_item;
      }

      const formatted_action = this.getFormattedAction(this.user_input);
      return {
        player_action: formatted_action,
        selected_item: item,
        use_d20: this.use_d20,
        action_type: this.action_type
      };
    },
    async createNewAsset() {
      const parent = this.$parent;
      const type = this.new_asset_type;
      const name = this.user_input.trim();
      const contextCards = parent.$refs.contextCards;

      if (!name) {
        parent.status_message = 'Error: Please set name for new story asset.';
        return;
      }

      // Get most recent story content to use as context for asset generation
      const context = parent.story_editor_content.slice(-1000).trim();

      // Use active_requests to disable buttons
      parent.active_requests++;
      this.loading = true;
      parent.status_message = 'Generating new asset...';

      // If this is not the only active component, do not edit parent messages
      const only_active = parent.active_requests === 1;
      try {
        if (type === 'inventory item') {
          // Generate new item and add to inventory
          const add = await parent.$refs.inventory.generateInventoryItem(type, name, context, this.new_item_equipped);
          
          // Return if errors occur during generation
          if (!add) {
            return;
          }
          // Change status message
          if (only_active && this.new_item_equipped) {
            parent.status_message = `Equipped item '${name}'.`;
          }
          else if (only_active) {
            parent.status_message = `Got item '${name}'.`;
          }
          this.reset(false);
          return;
        }
        // Generate and add new context card
        const action = await contextCards.generateContextCard(type, name, context, this.new_character_memories);

        if (!action) {
          parent.status_message = "Error: Creating asset failed. Check Context Cards tab."
        }

        // Set status message
        if (only_active && ['location', 'character', 'item'].includes(type)) {
          parent.status_message = `Created new ${type} card called '${name}'.`;
        }
        else if (only_active) {
          parent.status_message = `Created new card called '${name}'.`;
        }
        // Reset input for next action
        this.reset(false);
      } catch (err) {
        parent.status_message = 'Error creating asset: ' + (err.message || err);
      } finally {
        this.loading = false;
        parent.active_requests--;
      }
    }
  },
  computed: {
    inputPlaceholder() {
      switch (this.action_type) {
        case 'do': return 'What do you do?';
        case 'say': return 'What do you say?';
        case 'use': return 'How do you use the item?';
        case 'new': return 'Input name';
        default: return 'Input action';
      }
    },
    inventory() {
      return this.$parent.$refs.inventory?.inventory || [];
    }
  }
}
</script>

<template>
  <div class="action-controls-row">
    <select class="action-select" v-model="action_type">
      <option value="custom">Custom</option>
      <option value="do">Do</option>
      <option value="say">Say</option>
      <option value="use">Use</option>
      <option value="new">New</option>
    </select>

    <select class="item-select" v-if="action_type === 'use'" v-model="selected_item">
      <option value="">Select an item...</option>
      <option v-for="item in inventory" :key="item.id" :value="item">
        {{ item.name }}
      </option>
    </select>

    <select class="type-select" v-if="action_type === 'new'" v-model="new_asset_type">
      <option value="other">Other</option>
      <option value="character">Character</option>
      <option value="location">Location</option>
      <option value="item">Item (context card)</option>
      <option value="inventory item">Item (inventory)</option>
    </select>

    <select class="type-select" v-if="new_asset_type === 'inventory item'" v-model="new_item_type">
      <option value="other">Other</option>
      <option value="perishable">Perishable</option>
      <option value="weapon">Weapon</option>
      <option value="apparel">Armor/apparel</option>
    </select>

    <input
      v-model="user_input"
      type="text"
      spellcheck="true"
      :placeholder="inputPlaceholder"
    />

    <label v-if="new_asset_type === 'inventory item' && new_item_type !== 'perishable'">
      ⚔️: 
      <input
        v-model="new_item_equipped"
        type="checkbox"
        class="custom-checkbox"
        title="Equip item."
      />
    </label>

    <label v-if="new_asset_type === 'character'">
      📖: 
      <input
        v-model="new_character_memories"
        type="checkbox"
        class="custom-checkbox"
        title="Enable memory generation for character."
      />
    </label>

    <button v-if="action_type === 'new'" @click="createNewAsset" :disabled="loading">Add</button>

    <label v-if="action_type !== 'new'">
      <input 
        v-model="use_d20" 
        type="checkbox" 
        class="custom-checkbox"
        title="D20: If checked, actions will have a random chance to succeed or fail." 
      />
      🎲
    </label>
  </div>
</template>

<style>
.action-input-row {
  display: flex;
  width: 100%;
  gap: 8px;
}
.action-input-row input {
  flex: 1;
  width: 100%;
}

.action-controls-row {
  display: flex;
  width: 100%;
  gap: 2px;
  align-items: center;
  margin-bottom: 10px;
}

.action-select {
  min-width: 50px;
  max-width: 100px;
}
.item-select,
.type-select {
  min-width: 50px;
  max-width: 150px;
}

.action-controls-row button {
  height: 100%;
  margin: 2px;
}

.action-controls-row input[type="text"] {
  flex: 1;
}

.action-controls-row input[type="checkbox"] {
  margin: 0 4px;
}

.action-controls-row label {
  margin-right: 2px;
}

.action-controls-row span {
  margin-left: 2px;
}
</style>
