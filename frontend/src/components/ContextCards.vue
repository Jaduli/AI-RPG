<script>
import ContextCard from './ContextCard.vue';

export default {
  props: {
    mem_model: String,
    use_local: Boolean,
    show_token_use: Boolean,
    is_loading: Boolean
  },
  data() {
    return {
      collapse: false,
      cards: [],
      name: '',
      content: '',
      keywords: '',
      filter_type: 'all',
      type: 'other',
      // Type-specific values:
      parent_location: '',
      child_locations: '',
      equipped: false,
      create_memories: true
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
        keywords: this.keywords
      };
      if (type === 'location') {
        payload.parent_location = this.parent_location.trim();
        payload.child_locations = this.child_locations.trim();
      }
      if (type === 'character' || type === 'location') {
        payload.create_memories = this.create_memories;
        payload.memories = [];
      }
      // Split, trim, and remove empty keywords to avoid accidental empty-string matches
      payload.keywords = this.keywords
        .split(',')
        .map(k => k.trim())
        .filter(k => k.length > 0);
      
      this.cards.push(payload);
      this.name = '';
      this.content = '';
      this.keywords = '';
      this.child_locations = '';
    },
    // Function to normalize strings for matching keywords in story content. 
    // It lowercases the string, removes punctuation, and adds spaces at the 
    // start and end to prevent partial word matches.
    // Function made with ChatGPT-5.
    normalizeForMatch(str) {
      return ' ' + (str || '').toLowerCase()
        .replace(/[^\p{L}\p{N}\s']/gu, ' ')
        .replace(/\s+/g, ' ')
        .trim() + ' ';
    },
    // Function to suffle array to randomize chosen cards & card memories
    shuffleArray(array) {
      const result = [...array];
      for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
      }
      return result;
    },
    // Get matching context cards based on keywords in recent story content.
    // Cards are formatted to a string to be used in story generation.
    // If card type is character and its memories are enabled, up to 3 random
    // memories of given character are added as context.
    getMatchingContextCardsStr(text) {
      const matching = [];
      const normalized_text = this.normalizeForMatch(text);

      for (const card of this.cards) {
        if (card.keywords.length === 0) continue; // skip empty keyword fields

        // Check if any keyword is in the text
        for (const keyword of card.keywords) {
          let kw = (keyword || '').trim().toLowerCase();
          if (!kw) continue; // skip empty keywords

          kw = this.normalizeForMatch(kw);

          if (normalized_text.includes(kw)) {
            const payload = {
              name: card.name || '',
              type: card.type || '',
              content: card.content || '',
              parent_location: card.parent_location || '',
              child_locations: card.child_locations || '',
              memories: card.memories || []
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
      // Example formatted character card below.
      //
      // Colin, character:
      // A talented swordsman.
      // Memories for Colin:
      // - "I enjoyed my conversation with Luna."
      let card_text = '';

      for (const card of matching) {
        card_text += `${card.name}`;

        if (card.type !== 'other') {
          card_text += `, ${card.type}`;
        }

        if (card.parent_location) {
          card_text += ' in ' + card.parent_location;
        }
        card_text += ':\n' + card.content + '\n';
        if (card.child_locations) {
          card_text += `\nLocations within ${card.name}: ${card.child_locations}.\n`
        }
        if (card.memories) {
          // Get up to three random card memories as context
          const random_memories = this.shuffleArray(card.memories).slice(0, 3);

          if (random_memories.length > 0) {
            card_text += `\nMemories for ${card.name}:\n`
            
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
        parent.active_requests++;

        const story_information = parent.essential_context;
        
        // Only edit status message if this is the only active component
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
            story_information,
            recent_story
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
          if (data.tokens_total && parent.show_token_use) {
            parent.status_message = 'Tokens used for content generation: ' + data.tokens_total;
          } 
          else {
            parent.status_message = '';
          }
        }
      } finally {
         false;
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
    async generateContextCard(type = 'other', name = '', recent_story = '', create_memories = false) {
      this.name = name.trim();
      this.type = type;
      this.create_memories = create_memories;

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
    // Generate and add memories for existing context cards found in given content.
    // The first keyword is used for matching. The chance of creating is 1, then decreases
    // with each memory to make sure the card has at least one memory when first interacted with,
    // allowing the story to remember if a character has been met or a location been visited.
    // RPG mode uses player information and creates a memory relating to the player.
    async addCardMemory(recent_story, type) {
      const parent = this.$parent;
      const gamemode = parent.gamemode; // Gamemode affects generation prompt

      // Get context cards of given type with memory creation turned on
      let cards = this.cards.filter(
        card => card.create_memories === true && card.type === type
      );

      if (cards.length === 0) return;
      
      // Randomize order to prevent creating memories only for oldest cards
      cards = this.shuffleArray(cards)

      let card = null;
      const normalized_text = this.normalizeForMatch(recent_story);

      // Try to find one relevant card from text with the FIRST keyword.
      // This avoids triggering the card e.g. if a character has the keyword
      // of their home location.
      for (const c of cards) {
        if (c.keywords.length === 0) continue; // skip empty keyword fields

        // Check if first card keyword is found in recent story
        let kw = (c.keywords[0] || '')
        if (!kw) continue;

        kw = this.normalizeForMatch(kw);

        if (normalized_text.includes(kw)) {
          card = c;
        }
      }

      // Return if no card found
      if (!card) return;

      let chance = 0;
      const memory_count = Array.isArray(card.memories) ? card.memories.length : 0;

      // Ensure at least one memory, then decrease chance with each memory
      if (type === 'character') {
        chance = Math.max(1 / (memory_count + 1), 0.2); // Minimum 20% chance
      }
      // As location names appear less frequently in story content than characters, 
      // use a higher chance to create a new memory for location.
      else if (type === 'location') {
        chance = Math.max(1 - memory_count * 0.2, 0.4); // Minimum 40% chance
      }

      // Avoid memory generation every time a relevant card is found
      if (Math.random() > chance) return;

      parent.status_message = `Creating a ${card.type} memory...`;
      try {
        parent.active_requests++;

        // Get story information to use as context for memory generation
        const story_information =  parent.essential_context;

        let player_name = '';

        if (gamemode === 'rpg') {
          const player = parent.$refs.playerCard;

          if (!player || !player.name) {
            throw new Error('Please set player name for memory generation.');
          }
          player_name = player.name;
        }

        const res = await fetch('/api/generate_card_memory', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: this.mem_model,
            local: this.use_local,
            gamemode,
            story_information,
            player_name,
            card_type: card.type,
            card_name: card.name,
            card_description: card.content,
            recent_story
          })
        });
        const data = await res.json();

        if (data.error) {
          throw new Error(data.error);
        }
        
        const memory = data.new_memory;

        if (!memory) {
          throw new Error('Backend returned empty card memory.');
        }
        // Keep a maximum of 10 memories per card
        if (!Array.isArray(card.memories)) {
          card.memories = [];
        }
        if (card.memories.length >= 10) {
          // Remove the oldest memory
          card.memories.shift();
        }
        card.memories.push(memory);

        if (data.tokens_total && parent.show_token_use) {
          parent.status_message = 'Tokens used for card memory generation: ' + data.tokens_total;
        } 
        else {
          parent.status_message = '';
        }
        
      } finally {
        parent.active_requests--;
      }
    }
  },
  computed: {
    // Display cards from newest to oldest, filtered by selected type
    sortedCards() {
      let filtered = this.cards;
      if (this.filter_type !== 'all') {
        filtered = filtered.filter(card => card.type === this.filter_type);
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
        <button @click="handleGenerateContent"  :disabled="is_loading">Generate Content</button>
        <span title="Card name, type, and essential context will be used in content generation.">
          ⓘ
        </span>
      </label>

      <h4>Card Content</h4>
      <textarea v-model="content" />

      <h4>Keywords (comma-separated)</h4>
      <input type="text" v-model="keywords" maxlength="200" />

      <!-- Type-specific values -->
      <label v-if="type === 'location'">
        Parent Location: 
        <input type="text" v-model="parent_location" maxlength="200" />
      </label>

      <label v-if="type === 'location'">
        Child Locations: 
        <input type="text" v-model="child_locations" maxlength="300" />
      </label>

      <label v-if="type === 'character' || type === 'location'">
        Create Memories: 
        <input v-model="create_memories" type="checkbox" class="custom-checkbox" />
      </label>

      <button @click="addCard" :disabled="is_loading">Add Card</button>
    </div>
  </div>
  
  <div class="container">
    <div class="header-row">
      <h2>Existing Cards</h2>
      <label>Filter: 
      <select v-model="filter_type">
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
