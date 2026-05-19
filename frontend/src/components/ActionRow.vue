<script>
export default {
  data() {
    return {
      use_d20: false,
      selected_item: null,
      action_type: 'custom',
      action_input: '',
      input_placeholder: 'Input action'
    };
  },
  props: {
    gamemode: String,
  },
  methods: {
    // Reset values. Parameter all = false is used after a continue action
    // to keep item and type unchanged.
    reset(all = true) {
      this.action_input = '';
      this.use_d20 = false;
      if (all) {
        this.selected_item = null;
        this.action_type = 'custom';
      }
    },
    getPlayerAction() {
      var item = null;

      if (action_type === 'use') {
        item = this.selected_item;
      }

      return {
        user_action: this.getFormattedAction(this.action_input),
        selected_item: item,
        use_d20: this.use_d20,
        action_type: this.action_type
      };
    },
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
    getFormattedAction() {
      const type = this.action_type;
      let action = this.action_input.trim();

      // RPG elements added only if gamemode is rpg.
      if (this.gamemode !== 'rpg') {
        return action;
      }

      // Add punctuation if missing
      if (!/[.!?"]$/.test(action.trim())) {
        action += '.';
      }

      if (type === 'say') {
        if (!action.endsWith('"') || !action.startsWith('"')) {
          action = '"' + action + '"'
        }
        return 'You say ' + action;
      }

      if (type === 'do') {
        // Add "You" if missing (e.g. 'open the door -> You open the door')
        if (!/^you\b/i.test(action.trim())) {
          action = 'You ' + action;
        }
      }
      // Capitalize first letter
      action = action.charAt(0).toUpperCase() + action.slice(1);

      return action;
    }
  },
  computed: {
    inputPlaceholder() {
      switch (this.action_type) {
        case 'do': return 'What do you do?';
        case 'say': return 'What do you say?';
        case 'use': return 'How do you use the item?';
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
    </select>

    <select class="item-select" v-if="action_type === 'use'" v-model="selected_item">
      <option value="">Select an item...</option>
      <option v-for="item in inventory" :key="item.id" :value="item">
        {{ item.name }}
      </option>
    </select>

    <input
      v-model="action_input"
      type="text"
      spellcheck="true"
      :placeholder="inputPlaceholder"
    />

    <input v-model="use_d20" type="checkbox" class="custom-checkbox" />
    <span title="D20: If checked, actions will have a random chance to succeed or fail.">
      🎲
    </span>
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
.item-select {
  min-width: 50px;
  max-width: 150px;
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