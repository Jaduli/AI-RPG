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
            card_text += '\n';
          }
        }
        card_text += '\n';
      }
      return card_text;
    },
    removeCard(id) {
      this.cards = this.cards.filter(card => card.id !== id);
    },
    // Generate content with local or cloud AI. Can be done with or
    // without a name inserted.
    async generateContent(context = '') {
      try {
        this.loading = true;

        const parent = this.$parent;
        parent.active_requests++;
        
        // If this is not the only active component, do not edit parent messages
        const only_active = parent.active_requests === 1;

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
            context: context
          })
        });
        const data = await res.json();

        if (data.error) {
          this.content = 'Backend error creating content: ' + data.error;
          return false;
        }
        if (!data.generated_content) {
          this.content = 'Error: backend returned empty content.';
          return false;
        }
        this.content = data.generated_content;

        if (only_active) {
          parent.status_message = '';
        }
        return true;
      } catch (err) {
        this.content = 'Error creating content: ' + (err.message || err);
        return false;
      } finally {
        this.loading = false;
        parent.active_requests--;
      }
    },
    // Adds a new card based on given context, type, and name. Used in
    // ActionRow to create new cards based on recent story and user input.
    async generateContextCard(type = 'other', name = '', context = '', character_memories = false) {
      this.name = name.trim();
      this.type = type;
      this.create_memories = character_memories;

      // Add name as keyword
      this.keywords = name;

      // Clear other values
      this.parent_location = '';
      this.child_locations = '';

      // Only include most recent story as context if name is found
      if (!context.lower.includes(name.toLowerCase())) {
        context = '';
      }

      // Generate content with AI and add new card
      const generated = await this.generateContent(context);

      // Return if errors occur during generation
      if (!generated) {
        return;
      }
      this.addCard();
    },
    // Generate and add memories for existing characters found in given content.
    // Each continue action has a set chance of creating a character memory
    // if a character name is found in generated content (default: 30%).
    async addCharacterMemory(content, chance = 0.3) {
      const parent = this.$parent;

      // Get story content and gamemode from StoryEditor
      const gamemode = parent.gamemode; // Gamemode affects generation prompt

      // Get characters with memory creation turned on
      const characters = this.cards.filter(card => card.create_memories === true);

      // Create memory for first character found in content
      const character = characters.find(character =>
        content.includes(character.name)
      )
      // Return if no character found (not an error -> return true)
      if (!character) return true;

      // Only create memory sometimes (avoids exessive memory generation)
      if (Math.random() > chance) return true;

      parent.status_message = 'Creating character memory...';
      try {
        this.loading = true;

        // Get most recent story content to use as context for asset generation
        const recent_story = parent.story_editor_content.slice(-1000).trim();

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
            player: player,
            character_name: character.name,
            character_desctiption: character.content,
            recent_story: recent_story
          })
        });
        const data = await res.json();

        if (data.error) {
          parent.status_message = 'Backend error creating character memory: ' + data.error;
          return false;
        }
        
        const memory = data.new_memory;

        if (!memory) {
          parent.status_message = 'Error creating character memory: backend returned empty content.';
          return false;
        }
        // Keep a maximum of 10 memories per character
        if (this.character_memories.length > 10) {
          // Remove the oldest memory
          this.character_memories.shift();
        }
        this.character_memories.push(memory);

        return true;
      } catch (err) {
        parent.status_message = 'Error creating character memory: ' + (err.message || err);
        return false;
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
  <div class="context-cards">
    <h2>Add New Card</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>

    <div class="context-card" v-if="!collapse">
      <h4>Name</h4>
      <input type="text" v-model="name" maxlength="50" />

      <label>Type: 
        <select v-model="type">
          <option value="other">Other</option>
          <option value="character">Character</option>
          <option value="location">Location</option>
          <option value="item">Item</option>
        </select>
        <button @click="generateContent()"  :disabled="loading">Generate Content</button>
      </label>

      <h4>Content</h4>
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
    <div class="info-container">
    <h3>Existing Cards</h3>
    <h4>
      Cards with keywords matching recent story content will be included as context in story generation.
      Cards will automatically be saved when edited.
    </h4>
    </div>
    <label>Filter: 
      <select v-model="selected_type">
        <option value="all">All</option>
        <option value="character">Characters</option>
        <option value="location">Locations</option>
        <option value="object">Object</option>
        <option value="other">Other</option>
      </select>
    </label>

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
.context-card button {
  margin-bottom: 10px;
}
</style>
