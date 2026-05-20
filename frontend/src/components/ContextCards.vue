<script>
import ContextCard from './ContextCard.vue';

export default {
  props: {
    mem_model: String,
    use_local: Boolean,
    show_token_use: Boolean
  },
  data() {
    return {
      collapse: false,
      loading: false,
      cards: [],
      name: '',
      content: '',
      keywords: '',
      selected_type: 'all',
      type: 'other',
      // Type-specific values:
      parent_location: '',
      child_locations: '',
      equipped: false,
      create_memories: true,
      character_memories: []
    }
  },
  components: { ContextCard },
  methods: {
    // Add card with id, name, content, keywords (comma separated),
    // and type-specific values.
    addCard() {
      const type = this.type
      let payload = {
        id: Date.now(),
        name: this.name,
        type: type,
        content: this.content,
        
      };
      if (type === 'location' && this.parent_location?.trim()) {
        payload.parent_location = this.parent_location;
      }
      if (type === 'location' && this.child_locations?.trim()) {
        payload.child_locations = this.child_locations;
      }
      if (type === 'character' && this.create_memories) {
        payload.create_memories = this.create_memories;
        payload.character_memories = [];
      }
      payload.keywords = this.keywords.split(',')
      
      this.cards.push(payload);
      this.name = '';
      this.content = '';
      this.keywords = '';
      this.child_locations = '';
    },
    // Get matching context cards based on keywords in recent story content.
    // Cards are formatted to a string to be used in story generation.
    // If card type is character and its memories are enabled, up to 3 random
    // memories are added as context for each character.
    getMatchingContextCardsStr(text) {
      const lower_text = text.toLowerCase();
      const matching = [];

      for (const card of this.cards) {
        if (card.keywords.length === 0) continue; // skip empty keyword fields

        // Check if any keyword is in the text
        for (const keyword of card.keywords) {
          if (lower_text.includes(keyword.trim().toLowerCase())) {
            const payload = {
              name: card.name || '',
              type: card.type || '',
              content: card.content || '',
              parent_location: card.parent_location || '',
              child_locations: card.child_locations || '',
              character_memories: card.character_memories || []
            };
            matching.push(payload);
            break; // Only add card once even if multiple keywords match
          }
        }
        // To avoid adding too much context, stop if we have 10 matching cards
        if (matching.length >= 10) {
          break;
        }
      }

      if (matching.length === 0) return '';
      
      // Format matching cards into a string to be included in the prompt.
      // Example format
      // "Colin, character:
      //  A talented swordsman."
      let card_text = '';
      for (const card of matching) {
        card_text += `${card.name}, ${card.type}`;

        if (card.parent_location) {
          card_text += ' in ' + card.parent_location;
        }
        card_text += ':\n' + card.content + '\n';
        if (card.child_locations) {
          card_text += `Locations within ${card.name}: ${card.child_locations}\n`
        }
        if (card.character_memories) {
          // Get up to three random character memories as context
          const random_memories = [...card.character_memories]
            .sort(() => Math.random() - 0.5)
            .slice(0, 3);

          if (random_memories.length > 0) {
            card_text += `Memories for ${card.name}:\n`
            
            for (const memory of random_memories) {
              card_text += `-  ${memory}\n`;
            }
          }
        }
        card_text += '\n';
      }
      return card_text.trim();
    },
    removeCard(id) {
      this.cards = this.cards.filter(card => card.id !== id);
    },
    // Generate content with local or cloud AI. Can be done with or
    // without a name inserted.
    async generateContent(recent_story = '') {
      const parent = this.$parent;
      const only_active = parent.active_requests === 0;

      try {
        this.loading = true;
        parent.active_requests++;

        const story_information = parent.essential_context;
        
        // If this is not the only active component, do not edit parent messages
        if (only_active) {
          parent.status_message = 'Generating content...';
        }
        const res = await fetch('/api/generate_asset', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: this.mem_model,
            local: this.use_local,
            type: this.type,
            name: this.name,
            story_information: story_information,
            recent_story: recent_story
          })
        });
        const data = await res.json();

        if (data.error) {
          throw new Error(data.error);
        }
        if (!data.generated_content) {
          throw new Error('Backend returned empty asset content.');
        }
        this.content = data.generated_content;

        if (only_active) {
          parent.status_message = '';
        }
        return;
      } finally {
        this.loading = false;
        parent.active_requests--;
      }
    },
    async handleGenerateContent() {
      try {
        await this.generateContent();
      } catch (err) {
        this.content = 'Error generating content: ' + (err.message || String(err));
      }
    },
    // Adds a new card based on given recent story, type, and name. Used in
    // ActionRow to create new cards based on recent story and user input.
    async generateContextCard(type = 'other', name = '', recent_story = '', character_memories = false) {
      this.name = name.trim();
      this.type = type;
      this.create_memories = character_memories;

      // Add name as keyword
      this.keywords = name;

      // Clear other values
      this.parent_location = '';
      this.child_locations = '';

      // Generate content with AI and add new card
      await this.generateContent(recent_story);
      this.addCard();
      return;
    },
    // Generate and add memories for existing characters found in given content.
    // Each continue action has a set chance of creating a character memory
    // if a character name is found in generated content (default: 30%).
    async addCharacterMemory(content, chance = 0.3) {
      const parent = this.$parent;

      // Get story content and gamemode from StoryEditor
      const gamemode = parent.gamemode; // Gamemode affects generation prompt

      // Get characters with memory creation turned on
      let characters = this.cards.filter(card => card.create_memories === true);

      if (characters.length === 0) return;
      
      // Randomize order to prevent creating memories only for oldest characters
      characters = [...characters].sort(() => Math.random() - 0.5)

      let character = null;
      const lower_content = content.trim().toLowerCase();

      // Try to find one relevant character from text
      for (const char of characters) {
        if (char.keywords.length === 0) continue; // skip empty keyword fields

        // Check if any character keyword is found in content
        for (const keyword of char.keywords) {
          if (lower_content.includes(keyword.trim().toLowerCase())) {
            character = char;
            break;
          }
          // Stop if relevant character found
          if (character) break;
        }
      }

      // Return if no character found
      if (!character) return;

      // Avoid memory generation every time a character is found
      if (Math.random() > chance) return;

      parent.status_message = 'Generating character memory...';
      try {
        this.loading = true;

        // Get story information to use as context for memory generation
        const story_information =  parent.essential_context;

        const player = '';

        if (gamemode === 'rpg') {
          // Get player name from player card
          const player = parent.playerCard.name;
        }

        const res = await fetch('/api/generate_character_memory', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: this.mem_model,
            local: this.use_local,
            gamemode: gamemode,
            story_information: story_information,
            player: player,
            character_name: character.name,
            character_desctiption: character.content,
            recent_story: recent_story
          })
        });
        const data = await res.json();

        if (data.error) {
          throw new Error(data.error);
        }
        
        const memory = data.new_memory;

        if (!memory) {
          throw new Error('Backend returned empty character memory.');
        }
        // Keep a maximum of 10 memories per character
        if (!Array.isArray(character.character_memories)) {
          character.character_memories = [];
        }
        if (character.character_memories.length > 10) {
          // Remove the oldest memory
          character.character_memories.shift();
        }
        character.character_memories.push(memory);
      } finally {
        this.loading = false;
      }
    }
  },
  computed: {
    // Display cards from newest to oldest, filtered by selected type
    sortedCards() {
      let filtered = this.cards;
      if (this.selected_type !== 'all') {
        filtered = filtered.filter(card => card.type === this.selected_type);
      }
      return [...filtered].reverse();
    }
  }
}
</script>

<template>
  <div class="header-row">
    <h2>Add New Card</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>
  </div>

  <div class="container">
    <div class="context-card" v-if="!collapse">
      <h4>Card Name</h4>
      <input type="text" v-model="name" maxlength="50" />

      <label>Type: 
        <select v-model="type">
          <option value="other">Other</option>
          <option value="character">Character</option>
          <option value="location">Location</option>
          <option value="item">Item</option>
        </select>
        <button @click="handleGenerateContent"  :disabled="loading">Generate Content</button>
        <span title="Card name and type will be used in content generation.">
          ⓘ
        </span>
      </label>

      <h4>Card Content</h4>
      <textarea v-model="content" />

      <h4>Keywords (comma-separated)</h4>
      <input type="text" v-model="keywords" maxlength="200" />

      <!-- Type-specific values -->
      <label v-if="type === 'character'">Create Character Memories: 
        <input v-model="create_memories" type="checkbox" class="custom-checkbox" />
      </label>

      <label v-if="type === 'location'">Parent Location: 
        <input type="text" v-model="parent_location" maxlength="200" />
      </label>

      <label v-if="type === 'location'">Child Locations (comma-seperated): 
        <input type="text" v-model="child_locations" maxlength="300" />
      </label>

      <button @click="addCard" :disabled="loading">Add Card</button>
    </div>
  </div>
  
  <div class="container">
    <div class="header-row">
      <h2>Existing Cards</h2>
      <label>Filter: 
      <select v-model="selected_type">
        <option value="all">All</option>
        <option value="character">Characters</option>
        <option value="location">Locations</option>
        <option value="object">Object</option>
        <option value="other">Other</option>
      </select>
      </label>
    </div>

    <p v-if="sortedCards.length === 0">
      No Cards.
    </p>

    <ContextCard
      v-for="card in sortedCards"
      :key="card.id"
      :card="card"
      @remove="removeCard(card.id)"
    />
  </div>
</template>

<style>
.context-cards {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-cards > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
}
.context-card h4 {
  margin: 3px 0 3px;
}
.context-card textarea {
  min-height: 120px;
}
.context-card input {
  margin: 4px;
}
.context-card button {
  margin-bottom: 10px;
}
</style>
